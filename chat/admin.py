from django.contrib import admin
from .models import FriendRequest, Friendship, Thread, Message

admin.site.register(FriendRequest)
admin.site.register(Friendship)
admin.site.register(Thread)
admin.site.register(Message)
