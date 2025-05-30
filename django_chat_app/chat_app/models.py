from django.db import models

# Create your models here.
from django.contrib.auth.models import User # Using Django's built-in User model

class ChatRoom(models.Model):
    """
    Represents a chat room, which can be a group chat or a private one-on-one chat.
    """
    name = models.CharField(max_length=255, unique=True, blank=True, null=True)
    # Members for group chats. For private chats, it will typically have 2 members.
    members = models.ManyToManyField(User, related_name='chat_rooms')
    is_private = models.BooleanField(default=False) # True for one-on-one chats

    def __str__(self):
        if self.is_private and self.members.count() == 2:
            # For private chats, display names of the two participants
            member_names = [member.username for member in self.members.all()]
            return f"Private Chat: {member_names[0]} & {member_names[1]}"
        elif self.name:
            return self.name
        else:
            # Fallback for private chats without a specific name
            return f"Chat Room {self.id}"

    def get_private_chat_name(self, user1, user2):
        """
        Generates a consistent name for a private chat between two users.
        Ensures the order of usernames doesn't matter for finding the room.
        """
        return f"private_{'_'.join(sorted([user1.username, user2.username]))}"

    @classmethod
    def get_or_create_private_chat(cls, user1, user2):
        """
        Gets an existing private chat room between two users or creates a new one.
        """
        private_chat_name = cls().get_private_chat_name(user1, user2)
        room, created = cls.objects.get_or_create(
            name=private_chat_name,
            is_private=True
        )
        if created:
            room.members.add(user1, user2)
        return room

class Message(models.Model):
    """
    Represents a message sent within a chat room.
    """
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp'] # Order messages by time

    def __str__(self):
        return f'{self.sender.username}: {self.content[:50]}'
