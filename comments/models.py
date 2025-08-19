from django.db import models
from django.core.validators import RegexValidator, URLValidator
from django.core.exceptions import ValidationError

username_validator = RegexValidator(
    regex=r"^[A-Za-z0-9]+$",
    message="User Name должен содержать только латинские буквы и цифры."
)

ALLOWED_TAGS = ["a", "code", "i", "strong"]
ALLOWED_ATTRS = {"a": ["href", "title"]}

class Comment(models.Model):
    parent = models.ForeignKey(
        "self",
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="children"
    )
    user_name = models.CharField(max_length=30, validators=[username_validator])
    email = models.EmailField()
    home_page = models.URLField(blank=True, validators=[URLValidator()])
    text_raw = models.TextField()
    text_html = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["parent", "created_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user_name"]),
            models.Index(fields=["email"]),
        ]
        ordering = ["-created_at"]

    def clean(self):
        if not self.text_raw.strip():
            raise ValidationError("Текст сообщения обязателен.")

    def __str__(self):
        return f"{self.user_name}: {self.text_raw[:30]}"
