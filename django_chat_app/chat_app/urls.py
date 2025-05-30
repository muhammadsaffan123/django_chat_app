from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), # Main chat index
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('room/<str:room_name>/', views.room, name='room'), # Specific chat room
    path('create_group_chat/', views.create_group_chat, name='create_group_chat'),
    path('private_chat/<str:recipient_username>/', views.start_private_chat, name='start_private_chat'),
]
