from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from .models import FeedPost, PostLike, PostComment, PostType
from .serializers import FeedPostSerializer, CreateFeedPostSerializer, PostCommentSerializer

class FeedListCreateAPIView(APIView):
    """
    Community Feed:
    GET /api/feed/ - Returns chronological timeline of stories and Strava activity cards.
    POST /api/feed/ - Posts a new volunteer story or reflection.
    """
    def get(self, request):
        post_type = request.query_params.get('type')
        posts = FeedPost.objects.select_related('author', 'activity', 'event').prefetch_related('comments', 'comments__author')
        if post_type:
            posts = posts.filter(post_type=post_type)

        serializer = FeedPostSerializer(posts, many=True, context={'request': request})
        return Response({
            'count': posts.count(),
            'posts': serializer.data
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'You must be logged in to post.'}, status=status.HTTP_401_UNAUTHORIZED)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Post content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        media_url = request.data.get('media_url', '')
        event_id = request.data.get('event_id')

        post = FeedPost.objects.create(
            author=request.user,
            post_type=PostType.USER_POST,
            content=content,
            media_url=media_url if media_url else None,
            event_id=event_id if event_id else None
        )
        serializer = FeedPostSerializer(post, context={'request': request})
        return Response({
            'success': True,
            'message': 'Post shared to the community feed!',
            'post': serializer.data
        }, status=status.HTTP_201_CREATED)

class ToggleLikeAPIView(APIView):
    """
    Toggles like on a post.
    POST /api/feed/posts/<id>/like/
    """
    def post(self, request, post_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Login required.'}, status=status.HTTP_401_UNAUTHORIZED)

        post = FeedPost.objects.filter(id=post_id).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        like = PostLike.objects.filter(post=post, user=request.user).first()
        if like:
            like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            post.save(update_fields=['likes_count'])
            is_liked = False
        else:
            PostLike.objects.create(post=post, user=request.user)
            post.likes_count += 1
            post.save(update_fields=['likes_count'])
            is_liked = True

        return Response({
            'is_liked': is_liked,
            'likes_count': post.likes_count
        })

class AddCommentAPIView(APIView):
    """
    Adds a comment to a feed post.
    POST /api/feed/posts/<id>/comment/
    """
    def post(self, request, post_id):
        if not request.user.is_authenticated:
            return Response({'error': 'Login required.'}, status=status.HTTP_401_UNAUTHORIZED)

        post = FeedPost.objects.filter(id=post_id).first()
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': 'Comment cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        comment = PostComment.objects.create(
            post=post,
            author=request.user,
            text=text
        )

        post.comments_count += 1
        post.save(update_fields=['comments_count'])

        return Response({
            'success': True,
            'comment': PostCommentSerializer(comment).data,
            'comments_count': post.comments_count
        }, status=status.HTTP_201_CREATED)
