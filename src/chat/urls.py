from django.urls import path

app_name = "chats"
from . import views


urlpatterns = [
    path(
        "create/",
        views.CreateChatAndMessageView.as_view(),
        name="create_chat_and_message",
    ),
    path(
        "chat_list/json/", views.ChatListJsonView.as_view(), name="chat_list_json"
    ),  # Новый URL для JSON
    path(
        "chat_list/", views.ChatListView.as_view(), name="chat_list"
    ),  # Стандартный URL для HTML
    path("chats/<slug:pk>/", views.ChatDetailView.as_view(), name="chat_detail"),
    path(
        "create-message/", views.ChatMessageCreateView.as_view(), name="create_message"
    ),
    path(
        "chats/<uuid:chat_id>/messages/",
        views.ChatMessagesView.as_view(),
        name="chat_messages",
    ),
    path(
        "ajax/create-private-chat/",
        views.create_or_get_private_chat,
        name="create_private_chat",
    ),
]
