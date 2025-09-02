from __future__ import annotations

from django.core.cache import cache
import hashlib
from typing import Optional, List
from datetime import datetime

import strawberry
from strawberry import ID
from strawberry.types import Info
from strawberry.file_uploads import Upload

from enum import Enum

from django.core.files.uploadedfile import UploadedFile

from django.db.models import Count
from .models import Comment, User, Attachment

from .utils import sanitize_comment_html, verify_captcha


def _get_client_ip_and_ua(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        ip = xff.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    ua = request.META.get("HTTP_USER_AGENT", "")
    return ip, ua


@strawberry.enum
class OrderField(Enum):
    CREATED_AT = "CREATED_AT"
    AUTHOR_NAME = "AUTHOR_NAME"
    AUTHOR_EMAIL = "AUTHOR_EMAIL"
    USER_NAME = "USER_NAME"
    EMAIL = "EMAIL"


@strawberry.type
class AttachmentType:
    id: ID
    url: str
    contentType: Optional[str]
    size: int
    width: Optional[int]
    height: Optional[int]
    isImage: bool

    @staticmethod
    def from_model(a: Attachment) -> "AttachmentType":
        return AttachmentType(
            id=a.id,
            url=a.file.url,
            contentType=a.content_type or None,
            size=a.size or 0,
            width=a.width,
            height=a.height,
            isImage=a.is_image,
        )


@strawberry.type
class UserType:
    id: ID
    name: str
    email: str
    homePage: Optional[str] = None

    @staticmethod
    def from_model(u: User) -> "UserType":
        return UserType(
            id=str(u.id),
            name=u.name,
            email=u.email,
            homePage=u.home_page or None,
        )


@strawberry.type
class CommentType:
    id: ID
    author: UserType
    parentId: Optional[ID]
    textRaw: str
    textHtml: Optional[str] = None
    createdAt: datetime
    repliesCount: int

    @strawberry.field
    def attachments(self, info: Info) -> List[AttachmentType]:
        try:
            rows = Attachment.objects.filter(comment_id=self.id).order_by("id")
            return [AttachmentType.from_model(a) for a in rows]
        except Exception:
            return []

    @staticmethod
    def from_model(c: Comment) -> "CommentType":
        return CommentType(
            id=c.id,
            author=UserType.from_model(c.author),
            parentId=c.parent_id,
            textRaw=c.text_raw,
            textHtml=c.text_html,
            createdAt=c.created_at,
            repliesCount=getattr(c, "replies_count", None) or c.children.count(),
        )


@strawberry.type
class CommentList:
    count: int
    results: List[CommentType]


@strawberry.type
class Query:
    @strawberry.field
    def comments(
        self,
        info: Info,
        page: int = 1,
        pageSize: int = 25,
        orderField: OrderField = OrderField.CREATED_AT,
        desc: bool = True,
        parentId: Optional[ID] = None,
    ) -> CommentList:
        qs = Comment.objects.select_related("author")
        if parentId is None:
            qs = qs.filter(parent__isnull=True)
        else:
            qs = qs.filter(parent_id=parentId)

        qs = qs.annotate(replies_count=Count("children"))

        order_map = {
            OrderField.CREATED_AT: "created_at",
            OrderField.AUTHOR_NAME: "author__name",
            OrderField.AUTHOR_EMAIL: "author__email",
            OrderField.USER_NAME: "author__name",
            OrderField.EMAIL: "author__email",
        }
        main = order_map.get(orderField, "created_at")
        prefix = "-" if desc else ""
        order_by = [f"{prefix}{main}", f"{prefix}id"]

        total = qs.count()
        start = max(page, 1) - 1
        start *= pageSize
        rows = list(qs.order_by(*order_by)[start: start + pageSize])

        return CommentList(
            count=total,
            results=[CommentType.from_model(c) for c in rows],
        )



@strawberry.input
class CreateCommentInput:
    userName: Optional[str] = None
    name: Optional[str] = None
    email: str
    homePage: Optional[str] = None
    text: str
    parentId: Optional[ID] = None
    captcha: str
    captchaKey: Optional[str] = None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_comment(self, info: Info, input: CreateCommentInput) -> CommentType:
        request = info.context["request"]
        ip, ua = _get_client_ip_and_ua(request)

        key = input.captchaKey or request.COOKIES.get('captcha_key')
        # key_from_input = getattr(input, "captchaKey", None)
        # key_from_cookie = request.COOKIES.get("captcha_key")
        # key = key_from_input or key_from_cookie
        # code = (input.captcha or "").strip()
        # norm = code.lower()
        # stored = cache.get(f"captcha:{key}")
        #
        # print(f"[CAPTCHA DEBUG] key_in={key_from_input} key_ck={key_from_cookie} use_key={key}")
        # print(f"[CAPTCHA DEBUG] code='{code}' norm='{norm}' stored?={stored is not None}")
        # if stored:
        #     print(f"[CAPTCHA DEBUG] stored[:10]={str(stored)[:10]}")
        #     print(f"[CAPTCHA DEBUG] match_hash={stored == hashlib.sha256(norm.encode()).hexdigest()}")
        #     print(f"[CAPTCHA DEBUG] match_raw ={stored == norm}")
        #
        # breakpoint()
        if not verify_captcha(key, input.captcha):
            raise Exception("Captcha invalid or expired")

        user_name = input.userName or input.name
        if not user_name:
            raise Exception("userName (or name) is required")

        user = User.objects.create(
            name=user_name,
            email=input.email,
            home_page=input.homePage or "",
            ip=ip or "0.0.0.0",
            user_agent=ua,
        )

        html = sanitize_comment_html(input.text)
        obj = Comment.objects.create(
            author=user,
            parent_id=int(input.parentId) if input.parentId else None,
            text_raw=input.text,
            text_html=html,
            ip=ip or None,
            user_agent=ua,
        )
        return CommentType.from_model(obj)

    @strawberry.mutation
    def upload_attachment(self, info: Info, commentId: ID, file: Upload) -> AttachmentType:
        comment = Comment.objects.get(pk=commentId)
        uploaded: UploadedFile = file

        att = Attachment(comment=comment)
        att.file.save(uploaded.name, uploaded, save=False)
        att.full_clean()
        att.save()
        return AttachmentType.from_model(att)


schema = strawberry.Schema(query=Query, mutation=Mutation)
