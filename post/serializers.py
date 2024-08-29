from rest_framework import serializers

from users.models import User
from post.models import Post, PostLike, PostComment, CommentLike


class UserSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'photo'
        ]


class PostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    post_likes_count = serializers.SerializerMethodField('get_post_likes_count')
    post_comments_count = serializers.SerializerMethodField('get_post_comments_count')
    me_liked = serializers.SerializerMethodField('get_me_liked')

    class Meta:
        model = Post
        fields = [
            'id',
            'author',
            'image',
            'description',
            'created_time',
            'post_likes_count',
            'post_comments_count',
            'me_liked'
        ]
        extra_kwargs = {
            'image': {'required': False},
        }

    def get_post_likes_count(self, obj):
        return obj.likes.count()

    def get_post_comments_count(self, obj):
        return obj.comments.count()

    def get_me_liked(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            try:
                PostLike.objects.get(author=request.user, post=obj)
                return True
            except PostLike.DoesNotExist:
                return False

        return False


class PostCommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all(), required=False)
    replies = serializers.SerializerMethodField('get_replies')
    comment_likes_count = serializers.SerializerMethodField('get_comment_likes_count')
    me_liked = serializers.SerializerMethodField('get_me_liked')


    class Meta:
        model = PostComment
        fields = [
            'id',
            'author',
            'comment',
            'post',
            'created_time',
            'parent',
            'replies',
            'comment_likes_count',
            'me_liked'
        ]

    def get_replies(self, obj):
        if obj.child.exists():
            serializer = self.__class__(obj.child.all(), many=True, context=self.context)
            return serializer.data
        return None

    def get_comment_likes_count(self, obj):
        return obj.likes.count()

    def get_me_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.likes.filter(author=user).exists()
        return None


class PostLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = [
            'id',
            'author',
            'post',
        ]


class CommentLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = [
            'id',
            'author',
            'comment',
        ]



