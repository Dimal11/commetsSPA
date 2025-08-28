import io, os
import uuid

from django.db import models
from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

username_validator = RegexValidator(
    regex=r"^[A-Za-z0-9]+$",
    message="User Name должен содержать только латинские буквы и цифры."
)

ALLOWED_TAGS = ["a", "code", "i", "strong"]
ALLOWED_ATTRS = {"a": ["href", "title"]}

MAX_IMAGE_SIZE = (320, 240)
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "GIF"}
MIME_BY_FORMAT = {"JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif"}

def _is_text_file(file, max_bytes=100 * 1024) -> bool:
    name = (getattr(file, "name", "") or "").lower()
    if not name.endswith(".txt"):
        return False
    pos = file.tell()
    try:
        if file.size > max_bytes:
            return False
        sample = file.read(min(file.size, 4096))
        if b"\x00" in sample:
            return False
        try:
            sample.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True
    finally:
        file.seek(pos)

def _open_image(file) -> Image.Image:
    pos = file.tell()
    try:
        img = Image.open(file)
        img.verify()
        file.seek(pos)
        img = Image.open(file)
        return img
    except Exception:
        file.seek(pos)
        raise ValidationError("Файл повреждён или не является поддерживаемым изображением.")

class Comment(models.Model):
    author = models.OneToOneField('comments.User', on_delete=models.CASCADE, related_name='comment')

    parent = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.CASCADE, related_name="children"
    )

    text_raw = models.TextField()
    text_html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["parent", "created_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["author"]),
        ]
        ordering = ["-created_at"]

    def clean(self):
        if not self.text_raw.strip():
            raise ValidationError("Текст сообщения обязателен.")

    def __str__(self):
        return f"{self.author.name}: {self.text_raw[:30]}"

class User(models.Model):
    name = models.CharField(max_length=30, validators=[username_validator])
    email = models.EmailField()
    home_page = models.URLField(blank=True, validators=[URLValidator()])

    ip = models.GenericIPAddressField()
    user_agent = models.TextField()

    class Meta:
        app_label = 'comments'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f'{self.name} <{self.email}>'

class Attachment(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/%d/")
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    is_image = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        f = self.file
        if not f:
            raise ValidationError("Файл обязателен.")

        try:
            img = _open_image(f)
            fmt = (img.format or "").upper()
            if fmt not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError("Допустимы только JPG, PNG или GIF.")
            self.is_image = True
            self.width, self.height = img.size
            self.content_type = MIME_BY_FORMAT[fmt]
            return
        except ValidationError:
            pass

        if _is_text_file(f):
            self.is_image = False
            self.width = self.height = None
            self.content_type = "text/plain; charset=utf-8"
            self.size = f.size
            return

        raise ValidationError("Разрешены только изображения (JPG/PNG/GIF) или TXT ≤ 100KB.")

    def save(self, *args, **kwargs):
        """
        Если файл — изображение: автоповорот по EXIF, масштаб до 320×240, оптимизация.
        Поля content_type/size/width/height/is_image — заполняются/актуализируются.
        """
        if self.file:
            try:
                img = _open_image(self.file)
                fmt = (img.format or "").upper()
                if fmt not in ALLOWED_IMAGE_FORMATS:
                    raise ValidationError("Допустимы только JPG, PNG или GIF.")
                self.is_image = True

                img = ImageOps.exif_transpose(img)
                orig_w, orig_h = img.size
                if orig_w > MAX_IMAGE_SIZE[0] or orig_h > MAX_IMAGE_SIZE[1]:
                    img.thumbnail(MAX_IMAGE_SIZE, Image.LANCZOS)

                buf = io.BytesIO()
                save_kwargs = {}
                if fmt == "JPEG":
                    save_kwargs.update(dict(quality=85, optimize=True, progressive=True))
                # Внимание: анимированный GIF здесь не сохраняем как анимированный.
                # Если нужно сохранить анимацию — потребуется отдельная логика.

                img.save(buf, format=fmt, **save_kwargs)
                buf.seek(0)

                base, _ext = os.path.splitext(self.file.name or "upload")
                ext = ".jpg" if fmt == "JPEG" else f".{fmt.lower()}"
                new_name = base + ext
                self.file.save(new_name, ContentFile(buf.read()), save=False)

                self.width, self.height = img.size
                self.size = self.file.size
                self.content_type = MIME_BY_FORMAT[fmt]
            except ValidationError:
                raise
            except Exception:
                self.is_image = False
                self.width = self.height = None
                self.size = self.file.size
                if not self.content_type:
                    self.content_type = "application/octet-stream"

        super().save(*args, **kwargs)
