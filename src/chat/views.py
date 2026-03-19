from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.utils.decorators import method_decorator
from rest_framework.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ChatMessage, ChatMessageMedia
from webmain.models import Seo
from .models import Chat
from django.utils import timezone
from django.views import View
from django.utils.timezone import now
from django.db.models import Prefetch
from django.db.models import Q

from useraccount.models import Profile


class CreateChatAndMessageView(View):
    def post(self, request, *args, **kwargs):
        # Получаем данные из формы
        content_type = request.POST.get("content_type")  # Тип контента
        object_id = request.POST.get("object_id")  # ID объекта
        owner_id = request.POST.get("owner")  # ID владельца чата
        message_content = request.POST.get(
            "message_content"
        )  # Содержание первого сообщения
        name = request.POST.get("name")  # Название чата

        # Отладочный вывод для проверки переданных данных
        print(
            f"Received data: content_type={content_type}, object_id={object_id}, owner_id={owner_id}, message_content={message_content}, name={name}"
        )

        # Проверка на обязательные поля
        if (
            not content_type
            or not object_id
            or not owner_id
            or not message_content
            or not name
        ):
            print("Error: Missing required fields")
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Получаем правильную модель пользователя
        User = get_user_model()

        try:
            # Проверяем, что владелец чата существует
            owner = User.objects.get(
                id=owner_id
            )  # Используем get_user_model() для получения пользователя
            print(f"Owner found: {owner.username}")  # Отладка: выводим имя владельца

            # Проверка на валидность названия чата
            if not isinstance(name, str) or not name.strip():
                print("Error: Invalid name field")
                return JsonResponse(
                    {"error": "Invalid name field. It should be a non-empty string."},
                    status=400,
                )

            # Преобразуем content_type в объект ContentType
            content_type_instance = ContentType.objects.get(
                model=content_type
            )  # Получаем ContentType по строке
            print(
                f"ContentType found: {content_type_instance}"
            )  # Отладка: выводим ContentType

            # Создаем новый чат
            chat = Chat.objects.create(
                owner=owner,  # Устанавливаем владельца как полученного пользователя
                name=name,
                created_at=timezone.now(),
                content_type=content_type_instance,  # Устанавливаем ContentType для чата
                object_id=object_id,  # Устанавливаем object_id для связи с объектом
            )
            print(f"Chat created: {chat.id}")

            # Добавляем текущего пользователя в поле 'users'
            chat.users.add(
                request.user
            )  # Добавляем текущего пользователя в список пользователей чата
            print(f"Current user {request.user.username} added to chat {chat.id}")

            # Создаем первое сообщение в чате
            message = ChatMessage.objects.create(
                chat=chat,
                content=message_content,
                author=request.user,
                status=0,  # Сообщение "Отправлено"
            )
            print(f"Message created: {message.id}")

            return JsonResponse(
                {
                    "status": "success",
                    "chat_id": str(chat.id),
                    "message_id": str(message.id),
                    "content": message.content,
                    "author": message.author.username,
                    "date": message.date.isoformat(),
                }
            )

        except User.DoesNotExist:
            print("Error: Owner user not found")
            return JsonResponse({"error": "Owner user not found"}, status=400)
        except ContentType.DoesNotExist:
            print("Error: Invalid content type")
            return JsonResponse({"error": "Invalid content type"}, status=400)
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse(
                {"error": f"Error creating chat or message: {str(e)}"}, status=400
            )


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class ChatListView(ListView):
    model = Chat
    template_name = "moderations/chat/chat_list.html"
    context_object_name = "chats"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(users=user).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today_date = now().date()  # Текущая дата для проверки

        # Добавляем форматированную дату и первого пользователя для каждого чата
        for chat in context["chats"]:
            # Форматируем дату/время для чата
            if chat.updated_at and chat.updated_at.date() == today_date:
                chat.formatted_date = chat.updated_at.strftime("%H:%M")  # Только время
            else:
                chat.formatted_date = (
                    chat.updated_at.strftime("%d/%m/%Y") if chat.updated_at else None
                )  # Только дата или None

            # Добавляем атрибут first_user (первый пользователь, кроме текущего)
            first_user = chat.users.exclude(id=user.id).first()
            setattr(chat, "first_user", first_user)

        # Добавляем SEO-данные
        # try:
        #     seo_data = Seo.objects.get(pagetype=12)
        #     context['seo_previev'] = seo_data.previev
        #     context['seo_title'] = seo_data.title
        #     context['seo_description'] = seo_data.metadescription
        #     context['seo_propertytitle'] = seo_data.propertytitle
        #     context['seo_propertydescription'] = seo_data.propertydescription
        # except Seo.DoesNotExist:
        #     context['seo_previev'] = None
        #     context['seo_title'] = None
        #     context['seo_description'] = None
        #     context['seo_propertytitle'] = None
        #     context['seo_propertydescription'] = None

        return context


class ChatListJsonView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        page = request.GET.get("page", 1)

        # Получаем чаты, связанные с текущим пользователем
        chats = Chat.objects.filter(users=user).distinct().order_by("-updated_at")

        # Пагинация: по 10 чатов на страницу
        paginator = Paginator(chats, 10)
        page_obj = paginator.get_page(page)

        # Формируем список чатов
        data = []
        current_date = now().date()  # Текущая дата
        for chat in page_obj.object_list:
            # Проверяем последнее сообщение
            last_message = chat.last_message
            last_message_content = (
                last_message.content
                if isinstance(last_message, ChatMessage)
                else "No messages"
            )

            # Форматируем дату/время
            formatted_date = None
            if chat.updated_at:
                chat_date = chat.updated_at.date()  # Получаем только дату из updated_at
                if chat_date == current_date:  # Если дата обновления сегодня
                    formatted_date = chat.updated_at.strftime("%H:%M")  # Только время
                else:  # Если дата обновления не сегодня
                    formatted_date = chat.updated_at.strftime("%d/%m/%Y")  # Только дата

            # Проверяем статус последнего сообщения
            if last_message:
                # Сообщение от текущего пользователя
                if last_message.author == user:
                    is_read = True
                    unread_count = 0
                    # Проверяем, есть ли в `views` только текущий пользователь
                    single_check = (
                        last_message.views.count() == 1
                        and last_message.views.filter(id=user.id).exists()
                    )
                else:
                    is_read = False
                    unread_count = chat.chatmessage.filter(~Q(views=user)).count()
                    single_check = (
                        False  # Не применимо для сообщений от других пользователей
                    )
            else:
                is_read = False
                unread_count = 0
                single_check = False

            # Получаем первого пользователя, кроме текущего
            other_user = chat.users.exclude(id=user.id).first()

            # Добавляем в список
            data.append(
                {
                    "id": chat.id,
                    "formatted_date": formatted_date,
                    "first_user": {
                        "username": other_user.username if other_user else "Unknown",
                        "avatar": other_user.avatar.url
                        if other_user and other_user.avatar
                        else None,
                    },
                    "last_message": last_message_content,
                    "is_read": is_read,
                    "unread_count": unread_count,
                    "single_check": single_check,  # Флаг для отображения одной галочки
                }
            )

        # Возвращаем JSON
        return JsonResponse(
            {"success": True, "chats": data, "has_next": page_obj.has_next()}
        )


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class ChatDetailView(DetailView):
    model = Chat
    template_name = "moderations/chat/chat_message.html"
    context_object_name = "chat"
    slug_field = "id"

    def get_queryset(self):
        user = self.request.user
        # Подгружаем сообщения и пользователей для оптимизации запросов
        return (
            Chat.objects.filter(users=user)
            .prefetch_related(
                "users",
                Prefetch(
                    "chatmessage",
                    queryset=ChatMessage.objects.select_related("author").order_by(
                        "-date"
                    )[:100],
                    to_attr="recent_messages",
                ),
            )
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chat = self.object  # Получаем текущий чат
        user = self.request.user  # Текущий пользователь

        # Обновляем просмотры для последних 100 сообщений
        recent_messages = getattr(chat, "recent_messages", [])
        for message in recent_messages:
            message.views.add(user)

        # Находим первого пользователя, кроме текущего
        other_user = chat.users.exclude(id=user.id).first()
        context["other_user"] = other_user

        # Добавляем SEO данные (если есть)
        try:
            seo_data = Seo.objects.get(pagetype=8)
            context["seo_previev"] = seo_data.previev
            context["seo_title"] = seo_data.title
            context["seo_description"] = seo_data.metadescription
            context["seo_propertytitle"] = seo_data.propertytitle
            context["seo_propertydescription"] = seo_data.propertydescription
        except Seo.DoesNotExist:
            context.update(
                {
                    "seo_previev": None,
                    "seo_title": None,
                    "seo_description": None,
                    "seo_propertytitle": None,
                    "seo_propertydescription": None,
                }
            )

        context["recent_messages"] = recent_messages
        return context


class ChatMessagesView(View):
    def get(self, request, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        chat = get_object_or_404(Chat, id=chat_id, users=request.user)

        # Получаем сообщения для данного чата в порядке от новых к старым
        messages = (
            ChatMessage.objects.filter(chat=chat)
            .select_related("author")
            .order_by("-date")
        )

        # Пагинация: по 20 сообщений на страницу
        page = request.GET.get("page", 1)
        paginator = Paginator(messages, 20)
        page_obj = paginator.get_page(page)

        # Формируем JSON-ответ
        data = [
            {
                "id": str(message.id),
                "author": {
                    "username": message.author.username
                    if message.author
                    else "Anonymous",
                    "avatar": message.author.avatar.url
                    if message.author and message.author.avatar
                    else None,
                },
                "content": message.content,
                "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                "is_current_user": message.author
                == request.user,  # Помечаем, если автор сообщения текущий пользователь
                "files": [
                    {
                        "url": media.file.url,
                        "filename": media.filename or media.file.name,
                        "is_image": media.file.name.lower().endswith(
                            (".png", ".jpg", ".jpeg", ".gif")
                        ),
                    }
                    for media in ChatMessageMedia.objects.filter(comment=message)
                ],
            }
            for message in page_obj.object_list
        ]

        return JsonResponse(
            {"success": True, "messages": data, "has_next": page_obj.has_next()}
        )


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class ChatMessageCreateView(CreateView):
    model = ChatMessage
    fields = ["chat", "content"]  # Убрано поле author, оно задаётся автоматически

    def form_valid(self, form):
        # Проверка доступа к чату
        chat = form.cleaned_data["chat"]
        if self.request.user not in chat.users.all():
            raise PermissionDenied("You do not have access to this chat.")

        # Устанавливаем текущего пользователя как автора сообщения
        form.instance.author = self.request.user
        self.object = form.save()

        # Если текущего пользователя нет в users чата, добавляем его
        if self.request.user not in self.object.chat.users.all():
            self.object.chat.users.add(self.request.user)

        # Обработка файлов (убраны проверки на тип и размер)
        media_files = self.request.FILES.getlist("files")
        for file in media_files:
            ChatMessageMedia.objects.create(
                comment=self.object, file=file, filename=file.name
            )

        # Возвращаем успешный JSON-ответ
        return JsonResponse(
            {
                "success": True,
                "message_id": str(self.object.id),
                "chat_id": str(self.object.chat.id),
                "content": self.object.content,
                "author": self.object.author.username,
            },
            status=201,
        )

    def form_invalid(self, form):
        # Возвращаем ошибки формы
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@login_required
def create_or_get_private_chat(request):
    if request.method == "POST":
        other_user_id = request.POST.get("user_id")
        if not other_user_id:
            return JsonResponse({"error": "User ID is required"}, status=400)

        other_user = get_object_or_404(Profile, id=other_user_id)
        current_user = request.user

        # Ищем существующий личный чат
        chat = (
            Chat.objects.filter(type=2, users=current_user)
            .filter(users=other_user)
            .distinct()
            .first()
        )

        if not chat:
            # Создаем новый чат
            chat = Chat.objects.create(type=2, owner=current_user)
            chat.users.add(current_user, other_user)
            chat.administrators.add(current_user)
            chat.save()

        return JsonResponse({"chat_url": f"/chat/chats/{chat.id}/"})

    return JsonResponse({"error": "Invalid request"}, status=400)
