# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from .models import ChatRoom, Message
from django.db.models import Q # For complex queries

def register_view(request):
    """
    Handles user registration.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log in the user after registration
            return redirect('index') # Redirect to the chat index page
    else:
        form = UserCreationForm()
    return render(request, 'chat/register.html', {'form': form})

def login_view(request):
    """
    Handles user login.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user) # Log in the user
            return redirect('index') # Redirect to the chat index page
    else:
        form = AuthenticationForm()
    return render(request, 'chat/login.html', {'form': form})

@login_required # Ensures only logged-in users can access this view
def logout_view(request):
    """
    Handles user logout.
    """
    logout(request)
    return redirect('login') # Redirect to login page after logout

@login_required
def index(request):
    """
    Displays a list of available chat rooms and online users.
    Allows users to create new group chats or start private chats.
    """
    # Get all public chat rooms
    public_chat_rooms = ChatRoom.objects.filter(is_private=False).order_by('name')

    # Get private chat rooms for the current user
    # This fetches rooms where the current user is a member and it's a private chat
    private_chat_rooms = ChatRoom.objects.filter(
        Q(members=request.user) & Q(is_private=True)
    ).distinct().order_by('name')

    # Get all other users for private chat initiation
    other_users = User.objects.exclude(id=request.user.id).order_by('username')

    context = {
        'public_chat_rooms': public_chat_rooms,
        'private_chat_rooms': private_chat_rooms,
        'other_users': other_users,
    }
    return render(request, 'chat/index.html', context)

@login_required
def room(request, room_name):
    """
    Displays a specific chat room.
    """
    # Get the chat room, ensuring it exists and the user is a member if private
    chat_room = get_object_or_404(ChatRoom, name=room_name)

    # For private rooms, ensure the current user is a member
    if chat_room.is_private and request.user not in chat_room.members.all():
        return redirect('index') # Redirect if not authorized for private room

    # Fetch last 50 messages for history
    messages = chat_room.messages.order_by('-timestamp')[:50]
    messages = reversed(messages) # Display oldest first

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'chat_room': chat_room,
        'messages': messages,
        'current_user': request.user,
    })

@login_required
def create_group_chat(request):
    """
    Handles the creation of new group chat rooms.
    """
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if room_name:
            # Create a new group chat room
            room, created = ChatRoom.objects.get_or_create(name=room_name, is_private=False)
            if created:
                room.members.add(request.user) # Add creator to the room
                # You might want to add other selected users here if implemented
            return redirect('room', room_name=room.name)
    return redirect('index') # Redirect back if no room name or GET request

@login_required
def start_private_chat(request, recipient_username):
    """
    Starts or opens an existing private chat with another user.
    """
    recipient = get_object_or_404(User, username=recipient_username)

    # Ensure users cannot start a private chat with themselves
    if request.user == recipient:
        # Optionally, display an error message or redirect to a different page
        return redirect('index')

    # Get or create the private chat room
    chat_room = ChatRoom.get_or_create_private_chat(request.user, recipient)

    return redirect('room', room_name=chat_room.name)

