from __future__ import annotations
from typing import Optional, List
from datetime import datetime

import strawberry
from strawberry import ID
from strawberry.types import Info

from django.db.models import Count
from .models import Comment, User

from .utils import sanitize_comment_html


def _get_client_ip_and_ua(request):
    # Простейшее извлечение IP/UA для записи в модели
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        ip = xff.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    ua = request.META.get("HTTP_USER_AGENT", "")
    return ip, ua


@strawberry.enum
class OrderField:
    AUTHOR_NAME = "author__name"
    AUTHOR_EMAIL = "author__email"
    CREATED_AT = "created_at"


@strawberry.type
class UserType:
    # UUID удобнее отдать как строку
    id: ID
    name: str
    email: str
    homePage: Optional[str]

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
    textHtml: str
    createdAt: datetime
    repliesCount: int

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

        order_clause = orderField.value
        if desc:
            order_clause = f"-{order_clause}"

        total = qs.count()
        start = (page - 1) * pageSize
        rows = list(qs.order_by(order_clause)[start : start + pageSize])

        return CommentList(
            count=total,
            results=[CommentType.from_model(c) for c in rows],
        )


@strawberry.input
class CreateCommentInput:
    # данные автора (лежат в User)
    userName: str
    email: str
    homePage: Optional[str] = None
    # данные комментария
    text: str
    parentId: Optional[ID] = None


@strawberry.type
class Mutation:
    @strawberry.mutation
    def createComment(self, info: Info, input: CreateCommentInput) -> CommentType:
        # request доступен в контексте strawberry.django GraphQLView
        request = info.context["request"]
        ip, ua = _get_client_ip_and_ua(request)

        # ВАЖНО: у тебя в моделях Comment.author = OneToOneField(User).
        # Это означает "один пользователь -> ровно один комментарий".
        # Поэтому создаём нового User на каждый комментарий.
        # Если хочешь, чтобы один пользователь мог оставить много комментариев,
        # поменяй OneToOneField на ForeignKey.
        user = User.objects.create(
            name=input.userName,
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


schema = strawberry.Schema(query=Query, mutation=Mutation)
