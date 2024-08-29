from django.urls import path

from post.views import PostListApiView, PostCreateApiView, \
    PostDetailApiView, PostUpdateApiView, PostDeleteApiView, \
    PostCommentListView, PostCommentCreateView, CommentListCreateView, \
    PostLikeListView, CommentDetailDeleteView, CommentLikeListView, \
    PostLikeApiView, CommentLikeApiView

urlpatterns = [
    path('list/', PostListApiView.as_view(), name='post_list'),
    path('create/', PostCreateApiView.as_view(), name='post_create'),
    path('<uuid:pk>/', PostDetailApiView.as_view(), name='post_detail'),
    path('<uuid:pk>/update/', PostUpdateApiView.as_view(), name='post_edit'),
    path('<uuid:pk>/delete/', PostDeleteApiView.as_view(), name='post_delete'),
    path('<uuid:pk>/likes/', PostLikeListView.as_view(), name='post_like_list'),
    path('<uuid:pk>/comments/', PostCommentListView.as_view(), name='post_comments'),
    path('<uuid:pk>/comments/create/', PostCommentCreateView.as_view(), name='post_comment_create'),
    path('<uuid:pk>/liking/', PostLikeApiView.as_view(), name='post_like_create_delete'),

    path('comments/', CommentListCreateView.as_view(), name='comment_list_create'),
    path('comments/<uuid:pk>/', CommentDetailDeleteView.as_view(), name='comment_detail_delete'),
    path('comments/<uuid:pk>/likes/', CommentLikeListView.as_view(), name='comment_like_list'),
    path('comments/<uuid:pk>/liking/', CommentLikeApiView.as_view(), name='comment_like_create_delete'),
]
