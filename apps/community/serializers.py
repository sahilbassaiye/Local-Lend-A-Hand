from rest_framework import serializers
from .models import FeedPost, PostLike, PostComment

class PostCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.CharField(source='author.profile_image_url', read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'author', 'author_name', 'author_username', 'author_avatar', 'text', 'created_at']

class FeedPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_role = serializers.CharField(source='author.role', read_only=True)
    author_avatar = serializers.CharField(source='author.profile_image_url', read_only=True)
    comments = PostCommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = FeedPost
        fields = [
            'id', 'author', 'author_name', 'author_username', 'author_role', 'author_avatar',
            'post_type', 'content', 'media_url', 'likes_count', 'comments_count',
            'activity_metadata', 'comments', 'is_liked', 'created_at'
        ]

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False

class CreateFeedPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedPost
        fields = ['content', 'media_url', 'event']

    def create(self, validated_data):
        user = self.context['request'].user
        return FeedPost.objects.create(author=user, **validated_data)
