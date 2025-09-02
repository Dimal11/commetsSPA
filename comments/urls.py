from django.urls import path
from .views import CommentCreateView, top_comments_list

urlpatterns = [
    path("comments/", CommentCreateView.as_view()),
    path("comments/top/", top_comments_list),
]
