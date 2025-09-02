import io, os
import mimetypes
import uuid

from django.db import models
from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

username_validator = RegexValidator(
    regex=r"^[A-Za-z0-9А-Яа-яЁё _\-.']+$",
    message="User Name должен содержать буквы (латиница/кириллица), цифры, пробелы и _-.'."
)

ALLOWED_TAGS = ["a", "code", "i", "strong"]
ALLOWED_ATTRS = {"a": ["href", "title"]}

MAX_TXT_SIZE = 100 * 1024
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

def _open_image(file):
    pos = file.tell()
    try:
        img = Image.open(file)
        img.verify()
        file.seek(pos)
        return Image.open(file)
    except Exception:
        file.seek(pos)
        return None

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
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    is_image = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        f = self.file
        if not f:
            raise ValidationError("Файл обязателен.")

        img = _open_image(f)
        if img is not None:
            fmt = (getattr(img, "format", "") or "").upper()
            if fmt not in ALLOWED_IMAGE_FORMATS:
                raise ValidationError("Допустимы только JPG, PNG или GIF.")
            self.is_image = True
            self.width, self.height = img.size
            self.content_type = MIME_BY_FORMAT[fmt]
            self.size = getattr(f, "size", None)
            return

        if _is_text_file(f):
            self.is_image = False
            self.width = self.height = None
            self.content_type = "text/plain; charset=utf-8"
            self.size = getattr(f, "size", None)
            return

        raise ValidationError("Разрешены только изображения (JPG/PNG/GIF) или TXT ≤ 100KB.")

    def save(self, *args, **kwargs):
        if not self.file:
            return super().save(*args, **kwargs)

        self.size = getattr(self.file, "size", None)
        guessed = mimetypes.guess_type(self.file.name)[0]
        self.content_type = getattr(self.file, "content_type", None) or guessed or ""

        img = _open_image(self.file)

        if img is None:
            self.is_image = False
            self.width = None
            self.height = None

            is_txt = (self.content_type == "text/plain") or self.file.name.lower().endswith(".txt")
            if not is_txt:
                raise ValidationError("Разрешены только изображения JPG/PNG/GIF или текстовый файл .txt.")
            if self.size and self.size > MAX_TXT_SIZE:
                raise ValidationError("Текстовый файл должен быть не больше 100 KB.")

            return super().save(*args, **kwargs)

        fmt = (getattr(img, "format", "") or "").upper()
        if fmt not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError("Допустимы только JPG, PNG или GIF.")

        self.is_image = True

        img = ImageOps.exif_transpose(img)
        img.thumbnail((320, 240))

        buf = io.BytesIO()
        save_fmt = "JPEG" if fmt == "JPEG" else fmt
        save_kwargs = {"optimize": True}
        if save_fmt == "JPEG":
            save_kwargs["quality"] = 85
        img.save(buf, format=save_fmt, **save_kwargs)
        buf.seek(0)

        base = self.file.name.rsplit(".", 1)[0]
        ext = {"JPEG": "jpg", "PNG": "png", "GIF": "gif"}[save_fmt]
        self.file.save(f"{base}.{ext}", ContentFile(buf.read()), save=False)

        self.width, self.height = img.size
        self.content_type = {"JPEG": "image/jpeg", "PNG": "image/png", "GIF": "image/gif"}[save_fmt]
        self.size = self.file.size

        return super().save(*args, **kwargs)
