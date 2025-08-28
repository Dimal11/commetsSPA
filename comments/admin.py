from django.contrib import admin
from .models import Comment, User, Attachment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "home_page", "ip")
    search_fields = ("name", "email")
    list_filter = ("ip",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author_name",
        "author_email",
        "short_text",
        "parent",
        "created_at",
    )
    list_select_related = ("author", "parent")
    search_fields = ("author__name", "author__email", "text_raw")
    list_filter = ("created_at",)
    ordering = ("-created_at",)

    @admin.display(description="User Name", ordering="author__name")
    def author_name(self, obj: Comment) -> str:
        return obj.author.name

    @admin.display(description="Email", ordering="author__email")
    def author_email(self, obj: Comment) -> str:
        return obj.author.email

    @admin.display(description="Text")
    def short_text(self, obj: Comment) -> str:
        txt = obj.text_raw or ""
        return (txt[:50] + "…") if len(txt) > 50 else txt


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "comment", "is_image", "content_type", "size", "width", "height", "created_at")
    list_select_related = ("comment",)
    search_fields = ("comment__author__name", "comment__text_raw")
    list_filter = ("is_image", "content_type", "created_at")
