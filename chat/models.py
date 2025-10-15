from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        User, related_name="sent_requests", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, related_name="received_requests", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({'accepted' if self.accepted else 'pending'})"


class Friendship(models.Model):
    user = models.ForeignKey(User, related_name="friendships", on_delete=models.CASCADE)
    friend = models.ForeignKey(
        User, related_name="related_to_friendships", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "friend")

    def __str__(self):
        return f"{self.user} ↔ {self.friend}"

    @staticmethod
    def are_friends(user1, user2) -> bool:
        return Friendship.objects.filter(
            user=user1, friend=user2
        ).exists() or Friendship.objects.filter(user=user2, friend=user1).exists()


class Thread(models.Model):
    """Represents a one-on-one chat thread between two users"""

    user1 = models.ForeignKey(
        User, related_name="thread_user1", on_delete=models.CASCADE
    )
    user2 = models.ForeignKey(
        User, related_name="thread_user2", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")

    def __str__(self):
        return f"Thread: {self.user1} & {self.user2}"

    def participants(self):
        return [self.user1, self.user2]

    def is_participant(self, user):
        return user in self.participants()

    def get_other_user(self, user):
        if user == self.user1:
            return self.user2
        elif user == self.user2:
            return self.user1
        return None


class Message(models.Model):
    thread = models.ForeignKey(Thread, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

    @staticmethod
    def count_between_nonfriends(user1, user2):
        """Count total messages exchanged between two users (any direction)."""
        from django.db.models import Q

        return Message.objects.filter(
            Q(sender=user1, thread__user2=user2)
            | Q(sender=user2, thread__user2=user1)
            | Q(sender=user1, thread__user1=user2)
            | Q(sender=user2, thread__user1=user1)
        ).count()
