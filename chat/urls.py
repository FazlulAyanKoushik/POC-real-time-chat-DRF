from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    SendFriendRequestView,
    RespondFriendRequestView,
    ListFriendsView,
    ListFriendRequestsView,
)

urlpatterns = [
    # Auth
    path("register/", RegisterView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Friend requests
    path("friend-request/send/", SendFriendRequestView.as_view(), name="send_friend_request"),
    path("friend-request/respond/<int:pk>/", RespondFriendRequestView.as_view(), name="respond_friend_request"),
    path("friend-request/list/", ListFriendRequestsView.as_view(), name="list_friend_requests"),
    path("friends/", ListFriendsView.as_view(), name="list_friends"),
]
