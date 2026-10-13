from django.contrib import admin
from .models import FeedPost, PostLike, PostComment

@admin.register(FeedPost)
class FeedPostAdmin(admin.ModelAdmin):
    list_display = ('author', 'post_type', 'likes_count', 'comments_count', 'created_at')
    list_filter = ('post_type',)
    search_fields = ('author__username', 'content')

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
