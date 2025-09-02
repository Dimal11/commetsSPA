from django.utils.translation.trans_real import translation
from django.db import transaction
from rest_framework import serializers
from .models import Comment, User
from .utils import sanitize_comment_html, verify_captcha

def validate_captcha(captcha_token: str, captcha_code: str) -> bool:
    # TODO: реализовать реальную проверку (Redis/сессии)
    return bool(captcha_token and captcha_code)

class CommentCreateSerializer(serializers.ModelSerializer):
    name = serializers.RegexField(regex=r'^[A-Za-z0-9]+$', max_length=30)
    email = serializers.EmailField()
    home_page = serializers.URLField(required=False, allow_blank=True)

    captchaKey = serializers.CharField(write_only=True, required=False, allow_blank=True)
    captcha = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Comment
        fields = (
            'parent',
            'text_raw',
            'name',
            'email',
            'home_page',
            'captcha_token',
            'captcha_code',
            'captchaKey',
            'captcha',
        )

    def validate(self, attrs):
        key = attrs.get('captchaKey') or attrs.get('captcha_token')
        code = attrs.get('captcha') or attrs.get('captcha_code')
        if not verify_captcha(key, code):
            raise serializers.ValidationError({'captcha': 'Неверная или просроченная капча.'})

        raw = (attrs.get("text_raw") or "").strip()
        if not raw:
            raise serializers.ValidationError({"text_raw": "Текст сообщения обязателен."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        for k in ('captchaKey', 'captcha'):
            validated_data.pop(k, None)

        name = validated_data.pop("name")
        email = validated_data.pop("email")
        home_page = validated_data.pop("home_page", "")

        raw = validated_data["text_raw"]
        html = sanitize_comment_html(raw)

        request = self.context.get("request")
        ip = request.META.get("REMOTE_ADDR") if request else None
        ua = request.META.get("HTTP_USER_AGENT", "") if request else ""

        author = User(
            name=name,
            email=email,
            home_page=home_page,
            ip=ip,
            user_agent=ua,
        )
        author.full_clean()
        author.save()

        comment = Comment(
            author=author,
            text_raw=raw,
            text_html=html,
            ip=ip,
            user_agent=ua,
            parent=validated_data.get("parent"),
        )
        comment.full_clean()
        comment.save()

        return comment