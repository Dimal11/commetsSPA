import base64

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from django.db.models import Count
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import Comment, Attachment
from .serializers import CommentCreateSerializer
from .utils import make_captcha


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


@csrf_exempt
def upload_attachment_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    comment_id = request.POST.get("commentId")
    f = request.FILES.get("file")
    if not comment_id or not f:
        return JsonResponse({"error": "Fields 'commentId' and 'file' are required"}, status=400)

    comment = get_object_or_404(Comment, pk=comment_id)

    try:
        att = Attachment(comment=comment, file=f)
        att.full_clean()
        att.save()
        return JsonResponse({
            "id": att.id,
            "url": att.file.url,
            "contentType": att.content_type,
            "isImage": att.is_image,
            "width": att.width,
            "height": att.height,
            "size": att.size,
        })
    except ValidationError as e:
        msgs = []
        if hasattr(e, "message_dict"):
            for v in e.message_dict.values():
                msgs.extend(v if isinstance(v, (list, tuple)) else [v])
        elif hasattr(e, "messages"):
            msgs = list(e.messages)
        else:
            msgs = [str(e)]
        return JsonResponse({"error": "; ".join(msgs) or "Validation error"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def captcha_json(request):
    key, img_b64 = make_captcha()
    return JsonResponse({'image_base64': img_b64, 'key': key})


def captcha_image(request):
    key, img_b64 = make_captcha()
    raw = img_b64.split(',', 1)[1]
    data = base64.b64decode(raw)
    resp = HttpResponse(data, content_type='image/png')
    resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp['Pragma'] = 'no-cache'
    resp['Expires'] = '0'
    resp.set_cookie(
        'captcha_key', key,
        max_age=300,
        path='/',
        httponly=True,
        samesite='Lax',
        secure=not settings.DEBUG,
    )
    return resp
