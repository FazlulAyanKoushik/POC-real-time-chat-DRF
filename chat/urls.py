from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    SendFriendRequestView,
    RespondFriendRequestView,
    ListFriendsView,
    ListFriendRequestsView,
    ThreadListCreateView,
    MessageListView,
    MessageCreateView,
)

urlpatterns = [
    # Auth
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Friend requests
    path("friend-request/send/", SendFriendRequestView.as_view(), name="send_friend_request"),
    path("friend-request/respond/<int:pk>/", RespondFriendRequestView.as_view(), name="respond_friend_request"),
    path("friend-request/list/", ListFriendRequestsView.as_view(), name="list_friend_requests"),
    path("friends/", ListFriendsView.as_view(), name="list_friends"),

    # Threads
    path("threads/", ThreadListCreateView.as_view(), name="thread_list_create"),

    # Messages
    path("threads/<int:thread_id>/messages/", MessageListView.as_view(), name="message_list"),
    path("threads/<int:thread_id>/messages/send/", MessageCreateView.as_view(), name="message_create"),
]
