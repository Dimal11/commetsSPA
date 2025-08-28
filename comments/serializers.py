from django.utils.translation.trans_real import translation
from django.db import transaction
from rest_framework import serializers
from .models import Comment, User
from .utils import sanitize_comment_html
import re

def validate_captcha(captcha_token: str, captcha_code: str) -> bool:
    # TODO: реализовать реальную проверку (Redis/сессии)
    return bool(captcha_token and captcha_code)

class CommentCreateSerializer(serializers.ModelSerializer):
    name = serializers.RegexField(regex=r'^[A-Za-z0-9]+$', max_length=30)
    email = serializers.EmailField()
    home_page = serializers.URLField(required=False, allow_blank=True)

    captcha_token = serializers.CharField(write_only=True)
    captcha_code = serializers.CharField(write_only=True)

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
        )

    def validate(self, attrs):
        if not validate_captcha(attrs.get('captcha_token'), attrs.get('captcha_code')):
            raise serializers.ValidationError({'captcha': 'Неверная капча.'})

        raw = attrs.get("text_raw", "") or ""
        if not raw.strip():
            raise serializers.ValidationError({"text_raw": "Текст сообщения обязателен."})

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("captcha_token", None)
        validated_data.pop("captcha_code", None)

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