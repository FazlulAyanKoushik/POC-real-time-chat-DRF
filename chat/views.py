# Create your views here.
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FriendRequest, Friendship, Thread, Message
from .serializers import RegisterSerializer, UserSerializer, FriendRequestSerializer, ThreadSerializer, \
    MessageSerializer

User = get_user_model()


# --- Registration ---
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = []


# --- Friend request actions ---
class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        to_user_id = request.data.get("to_user_id")
        if not to_user_id:
            return Response({"detail": "to_user_id is required"}, status=400)

        if str(request.user.id) == str(to_user_id):
            return Response({"detail": "You cannot send a friend request to yourself."}, status=400)

        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        fr, created = FriendRequest.objects.get_or_create(
            from_user=request.user, to_user=to_user
        )

        if not created:
            return Response({"detail": "Friend request already sent."}, status=400)

        return Response(FriendRequestSerializer(fr).data, status=201)


class RespondFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Accept or reject a friend request"""
        try:
            fr = FriendRequest.objects.get(id=pk, to_user=request.user)
        except FriendRequest.DoesNotExist:
            return Response({"detail": "Friend request not found."}, status=404)

        action = request.data.get("action")
        if action == "accept":
            fr.accepted = True
            fr.save()
            # Create reciprocal friendships
            Friendship.objects.get_or_create(user=fr.from_user, friend=fr.to_user)
            Friendship.objects.get_or_create(user=fr.to_user, friend=fr.from_user)
            return Response({"detail": "Friend request accepted."})
        elif action == "reject":
            fr.delete()
            return Response({"detail": "Friend request rejected."})
        return Response({"detail": "Invalid action."}, status=400)


class ListFriendsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        friend_ids = Friendship.objects.filter(user=self.request.user).values_list("friend", flat=True)
        return User.objects.filter(id__in=friend_ids)


class ListFriendRequestsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user, accepted=False)


# --- Threads ---
class ThreadListCreateView(generics.ListCreateAPIView):
    serializer_class = ThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Thread.objects.filter(user1=self.request.user) | Thread.objects.filter(user2=self.request.user)

    def perform_create(self, serializer):
        user2_id = self.request.data.get("user2_id")
        if not user2_id:
            raise PermissionDenied("user2_id is required")

        if int(user2_id) == self.request.user.id:
            raise PermissionDenied("Cannot create thread with yourself")

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            raise PermissionDenied("User not found")

        # Ensure thread doesn't already exist
        existing = Thread.objects.filter(user1=self.request.user, user2=user2) | Thread.objects.filter(user1=user2, user2=self.request.user)
        if existing.exists():
            raise PermissionDenied("Thread already exists")

        serializer.save(user1=self.request.user, user2=user2)


# --- Messages ---
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        thread_id = self.kwargs["thread_id"]
        try:
            thread = Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            raise PermissionDenied("Thread not found")

        if not thread.is_participant(self.request.user):
            raise PermissionDenied("You are not a participant of this thread")

        return thread.messages.all()


class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        thread_id = self.kwargs["thread_id"]
        try:
            thread = Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            raise PermissionDenied("Thread not found")

        if not thread.is_participant(self.request.user):
            raise PermissionDenied("You are not a participant of this thread")

        # Enforce 20-message limit for non-friends
        other_user = thread.get_other_user(self.request.user)
        if not Friendship.are_friends(self.request.user, other_user):
            total_messages = Message.count_between_nonfriends(self.request.user, other_user)
            if total_messages >= 20:
                raise PermissionDenied("Message limit reached for non-friends")

        serializer.save(thread=thread, sender=self.request.user)
