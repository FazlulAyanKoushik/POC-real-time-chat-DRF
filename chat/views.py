# Create your views here.
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FriendRequest, Friendship
from .serializers import RegisterSerializer, UserSerializer, FriendRequestSerializer

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
