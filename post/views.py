from rest_framework import status
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import serialize

from post.models import Post, PostComment, PostLike, CommentLike
from post.serializers import PostSerializer, PostCommentSerializer, PostLikeSerializer, CommentLikeSerializer
from shared.custom_pagination import CustomPagination


class PostListApiView(generics.ListAPIView):
    permission_classes = [AllowAny,]
    serializer_class = PostSerializer
    pagination_class = CustomPagination
    queryset = Post.objects.all()


class PostDetailApiView(generics.RetrieveAPIView):
    permission_classes = [AllowAny,]
    serializer_class = PostSerializer
    queryset = Post.objects.all()


class PostCreateApiView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = PostSerializer
    queryset = Post.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostUpdateApiView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = PostSerializer
    queryset = Post.objects.all()


class PostDeleteApiView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = PostSerializer
    queryset = Post.objects.all()

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        return Response(
        {
                'success': True,
                'message': 'Post successfully deleted.'
            }, status=status.HTTP_204_NO_CONTENT
        )


class PostCommentListView(generics.ListAPIView):
    permission_classes = [AllowAny,]
    serializer_class = PostCommentSerializer

    def get_queryset(self):
        post_id = self.kwargs['pk']
        queryset = PostComment.objects.filter(post__id=post_id)
        return queryset


class PostCommentCreateView(generics.CreateAPIView):
    serializer_class = PostCommentSerializer
    permission_classes = [IsAuthenticated,]
    queryset = PostComment.objects.all()

    def perform_create(self, serializer):
        post_id = self.kwargs['pk']
        post = get_object_or_404(Post, pk=post_id)
        serializer.save(post=post, author=self.request.user)


class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly,]
    serializer_class = PostCommentSerializer
    queryset = PostComment.objects.all()
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CommentDetailDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly,]
    serializer_class = PostCommentSerializer
    queryset = PostComment.objects.all()


class PostLikeListView(generics.ListAPIView):
    permission_classes = [AllowAny,]
    serializer_class = PostLikeSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        post_id = self.kwargs['pk']
        return PostLike.objects.filter(post__id=post_id)


class CommentLikeListView(generics.ListAPIView):
    permission_classes = [AllowAny,]
    serializer_class = CommentLikeSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        comment_id = self.kwargs['pk']
        return CommentLike.objects.filter(comment__id=comment_id)


class PostLikeApiView(APIView):

    def post(self, request, pk):
        try:
            post = get_object_or_404(Post, pk=pk)
            author = request.user
            if not PostLike.objects.filter(post=post, author=author).exists():
                post_like = PostLike.objects.create(
                    post=post,
                    author=author
                )
                serializer = PostLikeSerializer(post_like)
                data = {
                    'success': True,
                    'message': 'Post successfully liked',
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_201_CREATED)
            else:
                post_like = PostLike.objects.get(
                    post=post,
                    author=author
                )
                post_like.delete()
                data = {
                    'success': True,
                    'message': "Post LIKE successfully deleted",
                }
                return Response(data, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            data = {
                'success': False,
                'message': str(e),
                'data': None
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class CommentLikeApiView(APIView):

    def post(self, request, pk):
        try:
            comment = get_object_or_404(PostComment, pk=pk)
            author = request.user
            if not CommentLike.objects.filter(comment=comment, author=author).exists():
                comment_like = CommentLike.objects.create(
                    comment=comment,
                    author=author
                )
                serializer = CommentLikeSerializer(comment_like)
                data = {
                    'success': True,
                    'message': 'Comment successfully liked',
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_201_CREATED)
            else:
                comment_like = CommentLike.objects.get(
                    comment=comment,
                    author=author
                )
                comment_like.delete()
                data = {
                    'success': True,
                    'message': "Comment LIKE successfully deleted",
                }
                return Response(data, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            data = {
                'success': False,
                'message': str(e),
                'data': None
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


