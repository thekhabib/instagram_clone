from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MaxLengthValidator, FileExtensionValidator

from shared.models import BaseModel

User = get_user_model()

class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='posts_images/', validators=[FileExtensionValidator(
        allowed_extensions=['png', 'jpg', 'jpeg', 'heic', 'heif']
    )])
    description = models.TextField(validators=[MaxLengthValidator(2000)])

    class Meta:
        db_table = 'posts'
        verbose_name = 'post'
        verbose_name_plural = 'posts'

    def __str__(self):
        return f"'{self.description[:25]}' - post by {self.author}"


class PostComment(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='child',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"'{self.comment[:20]}' comment by {self.author}"


class PostLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'post'],
                name='unique_post_like'
            )
        ]


class CommentLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'comment'],
                name='unique_comment_like'
            )
        ]
