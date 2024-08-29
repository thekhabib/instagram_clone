from django.contrib import admin
from post.models import Post, PostComment, PostLike, CommentLike


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'description', 'created_time')
    search_fields = ('id', 'author__username', 'description')


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_time')
    search_fields = ('id', 'author__username', 'comment')


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_time')
    search_fields = ('id', 'author__username')


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'comment', 'created_time')
    search_fields = ('id', 'author__username')


