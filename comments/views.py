from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Prefetch

from .models import Comment
from .serializers import CommentCreateSerializer

class CommentPagination(PageNumberPagination):
    page_size = 25

class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.AllowAny]

SORT_MAP = {
    "user_name": "user_name",
    "-user_name": "-user_name",
    "email": "email",
    "-email": "-email",
    "created_at": "created_at",
    "-created_at": "-created_at",
}

@api_view(["GET"])
def top_comments_list(request):
    order = request.GET.get("order", "-created_at")
    order = SORT_MAP.get(order, "-created_at")

    qs = (
        Comment.objects
        .filter(parent__isnull=True)
        .select_related('author')
        .order_by(order)
        .annotate(replies_count=Count('children'))
        .prefetch_related('attachments')
    )
    paginator = CommentPagination()
    page = paginator.paginate_queryset(qs, request)
    data = [
        {
            "id": c.id,
            "user_name": c.user_name,
            "email": c.email,
            "home_page": c.home_page,
            "text_html": c.text_html,
            "created_at": c.created_at,
            "replies_count": c.replies_count,
        }
        for c in page
    ]
    return paginator.get_paginated_response(data)
