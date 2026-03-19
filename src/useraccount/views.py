from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_protect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.urls import reverse
from django.http import (
    JsonResponse,
    Http404,
)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
import json
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.sites.models import Site

# Models
from webmain.models import Seo
from moderation.models import Ticket, TicketComment, TicketCommentMedia
from useraccount.models import (
    Profile,
    Notification,
    Withdrawal,
    Cards,
    Company,
    PersonalGroups,
)
from django.contrib.auth import get_user_model

# Forms
from useraccount.forms import (
    UserProfileForm,
    CardsForm,
    PersonalGroupForm,
)
from moderation.forms import (
    TicketCommentForm,
    WithdrawForm,
    TicketWithCommentForm,
)
from _project.domainsmixin import DomainTemplateMixin
from webmain.models import SettingsGlobale

"""Личный кабинет"""


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class EditMyProfileView(DomainTemplateMixin, TemplateView, LoginRequiredMixin):
    template_name = "profile_edit.html"
    model = SettingsGlobale

    def get(self, request, *args, **kwargs):
        initial_data = {
            "birthday": request.user.birthday.strftime("%Y-%m-%d")
            if request.user.birthday
            else None
        }
        form = UserProfileForm(instance=request.user, initial=initial_data)
        password_form = PasswordChangeForm(user=request.user)  # Форма для смены пароля

        context = self.get_context_data(
            form=form, password_form=password_form, title="Личные данные"
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        password_form = PasswordChangeForm(data=request.POST, user=request.user)
        profile_success = False
        password_success = False

        # Обработка данных профиля
        if form.is_valid():
            form.save()
            profile_success = True
            messages.success(request, "Профиль обновлен успешно.")
        else:

            # Обновляем только валидные поля
            for field_name, value in form.cleaned_data.items():
                if field_name in form.fields:
                    # Проверяем, что поле валидное
                    try:
                        # Получаем поле модели
                        model_field = form.instance._meta.get_field(field_name)
                        # Обновляем только валидные поля
                        setattr(form.instance, field_name, value)
                        profile_success = True
                    except Exception:
                        # В случае ошибок пропускаем
                        pass
            # Сохраняем только обновленные поля
            form.instance.save(update_fields=[
                field for field in form.cleaned_data.keys()
                if field in form.fields
            ])
            messages.success(request, "Обновлены валидные поля профиля.")

        # Обработка смены пароля
        if not profile_success:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Пароль изменен успешно.")
                password_success = True
            else:
                messages.error(request, "Ошибка при смене пароля.")
                print("Password form errors:", password_form.errors)

        context = self.get_context_data(
            form=form, password_form=password_form, title="Личные данные"
        )
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(
            **kwargs
        )  # Вызов `super()` сохраняет функциональность
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=15).first()
        context["adresses"] = self.request.user.get_adresses()

        if seo_data:
            context["seo_previev"] = seo_data.previev
            context["seo_title"] = seo_data.title
            context["seo_description"] = seo_data.metadescription
            context["seo_propertytitle"] = seo_data.propertytitle
            context["seo_propertydescription"] = seo_data.propertydescription
        else:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None
        return context


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class NotificationView(ListView):
    model = Notification
    template_name = "site/useraccount/notification_list.html"
    context_object_name = "notificationes"
    paginate_by = 30

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        print(f"Notifications for user {self.request.user}: {queryset}")
        return queryset

    def get(self, request, *args, **kwargs):
        # Обновляем статус уведомлений перед отображением страницы
        with transaction.atomic():
            updated_rows = Notification.objects.filter(
                user=self.request.user,
                status=1,  # Статус "Не прочитан"
            ).update(status=2)  # Меняем на "Прочитан"
        print(
            f"Updated {updated_rows} notifications to read status."
        )  # Выводим количество обновленных строк для отладки
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            seo_data = Seo.objects.get(pagetype=11)
            context["seo_previev"] = seo_data.previev
            context["seo_title"] = seo_data.title
            context["seo_description"] = seo_data.metadescription
            context["seo_propertytitle"] = seo_data.propertytitle
            context["seo_propertydescription"] = seo_data.propertydescription
        except Seo.DoesNotExist:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None

        print(f"Context data: {context}")  # Выводим контекст для отладки

        return context


"""Тикеты"""


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class TicketsView(DomainTemplateMixin, LoginRequiredMixin, ListView):
    model = Ticket
    template_name = "tickets.html"
    context_object_name = "tickets"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        tickets = Ticket.objects.filter(author=user).order_by("-date")

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            tickets = tickets.filter(themas__icontains=search_name)

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            tickets = tickets.filter(id__icontains=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            tickets = tickets.filter(status=search_type)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                tickets = tickets.filter(date__date=search_date)
            except ValueError:
                pass

        return tickets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=1).first()

        context.update(
            {
                "seo_previev": getattr(seo_data, "previev", None),
                "seo_title": getattr(seo_data, "title", None),
                "seo_description": getattr(seo_data, "metadescription", None),
                "seo_propertytitle": getattr(seo_data, "propertytitle", None),
                "seo_propertydescription": getattr(
                    seo_data, "propertydescription", None
                ),
            }
        )

        return context


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class TicketCreateView(DomainTemplateMixin, LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketWithCommentForm
    template_name = "ticket_create.html"
    context_object_name = "ticket"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(SettingsGlobale, site__domain=current_domain)

    @transaction.atomic
    def form_valid(self, form):
        ticket = form.save(commit=False)
        ticket.author = self.request.user  # Устанавливаем автора тикета
        ticket.author_comments = self.request.user

        User = get_user_model()
        managers = User.objects.filter(type=2).annotate(
            ticket_count=Count("ticket_manager")
        )

        if managers.exists():
            ticket.manager = min(managers, key=lambda x: x.ticket_count)

        ticket.save()

        # Создаем первый комментарий, связанный с тикетом
        comment = TicketComment.objects.create(
            ticket=ticket,
            author_comments=self.request.user,
            content=form.cleaned_data["content"],
        )

        files = form.cleaned_data.get("files")
        if files:
            for file in files:
                TicketCommentMedia.objects.create(comment=comment, file=file)

        return redirect(reverse("useraccount:tickets"))

    def form_invalid(self, form):
        print(form.errors)  # Для отладки
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class TicketMessageView(DomainTemplateMixin, LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = "tickets_messages.html"
    context_object_name = "ticket"
    slug_field = "id"
    slug_url_kwarg = "pk"  # Или 'uuid', в зависимости от URLconf

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.object

        # Комментарии
        comments = (
            TicketComment.objects.filter(ticket=ticket).prefetch_related("media").all()
        )

        paginator = Paginator(comments, 10)
        page = self.request.GET.get("page")
        try:
            comments_paginated = paginator.page(page)
        except PageNotAnInteger:
            comments_paginated = paginator.page(1)
        except EmptyPage:
            comments_paginated = paginator.page(paginator.num_pages)

        context["ticket_comments"] = comments_paginated
        context["form"] = TicketCommentForm()
        context["paginator"] = paginator
        context["page_obj"] = comments_paginated

        # SEO данные через текущий домен
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=1).first()

        context["seo_previev"] = getattr(seo_data, "previev", None)
        context["seo_title"] = getattr(seo_data, "title", None)
        context["seo_description"] = getattr(seo_data, "metadescription", None)
        context["seo_propertytitle"] = getattr(seo_data, "propertytitle", None)
        context["seo_propertydescription"] = getattr(
            seo_data, "propertydescription", None
        )

        return context


@method_decorator(login_required(login_url="webmain:login"), name="dispatch")
class TicketDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:tickets")

    def post(self, request):
        data = json.loads(request.body)
        ticket_ids = data.get("ticket_ids", [])
        if ticket_ids:
            Ticket.objects.filter(id__in=ticket_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class TicketCommentCreateView(LoginRequiredMixin, CreateView):
    model = TicketComment
    form_class = TicketCommentForm

    @transaction.atomic
    def form_valid(self, form):
        ticket_id = self.kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, id=ticket_id)
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author_comments = self.request.user
        comment.save()

        files = self.request.FILES.getlist("files")
        for file in files:
            TicketCommentMedia.objects.create(comment=comment, file=file)

        return JsonResponse(
            {
                "status": "success",
                "comment": {
                    "id": comment.id,
                    "author_comments": comment.author_comments.username,
                    "content": comment.content,
                    "date": comment.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "files": [
                        {"name": media.file.name, "url": media.file.url}
                        for media in comment.media.all()
                    ],
                },
            }
        )

    def form_invalid(self, form):
        print(form.errors)  # Для отладки
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


class ReferralListView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = "site/useraccount/referrals_list.html"  # Укажите ваш шаблон
    context_object_name = "referrals"  # Имя переменной для использования в шаблоне

    def get_queryset(self):
        # Возвращаем список пользователей, у которых referral указывает на текущего пользователя
        return Profile.objects.filter(referral=self.request.user)


class StatisticView(TemplateView):
    template_name = "site/useraccount/statistic.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Существующая логика получения объявлений, бронирований и т.д.
        # user_advertisements = Advertisement.objects.filter(author=self.request.user)
        # context['user_advertisements'] = user_advertisements
        # context['advertisements_count'] = user_advertisements.count()
        #
        # advertisement_content_type = ContentType.objects.get_for_model(Advertisement)
        # booking_content_type = ContentType.objects.get_for_model(Booking)
        #
        # user_bookings = Booking.objects.filter(advertisement__in=user_advertisements).order_by('-create')[:10]
        # context['user_bookings'] = user_bookings
        #
        # user_chats = Chat.objects.filter(
        #     (Q(content_type=advertisement_content_type) & Q(object_id__in=[ad.id for ad in user_advertisements])) |
        #     (Q(content_type=booking_content_type) & Q(object_id__in=[booking.id for booking in user_bookings]))
        # ).order_by('-created_at')[:6]
        # context['user_chats'] = user_chats

        # ==============================================
        # Получаем компанию, где пользователь — директор
        # или входит в поле users (M2M).
        # ==============================================
        company = Company.objects.filter(
            Q(director=self.request.user) | Q(users=self.request.user)
        ).first()

        # Если компания существует, считаем пользователей
        if company:
            context["company_users_count"] = company.users.count()
        else:
            context["company_users_count"] = 0

        return context


User = (
    get_user_model()
)  # Если у вас AUTH_USER_MODEL = 'useraccount.Profile', это подхватит вашу модель


class CompanyView(View):
    template_name = "site/useraccount/company.html"
    paginate_by = 5  # Количество пользователей на странице

    def get(self, request, *args, **kwargs):
        """Показываем список пользователей (с пагинацией и поиском)."""
        company = self.get_company_or_404(request)
        page_obj = self.get_page_obj(request, company)

        context = {
            "company": company,
            "page_obj": page_obj,
            "search_query": request.GET.get("search", ""),
            "success": None,
            "error": None,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Обрабатываем:
         - Удаление пользователя (remove_user_id).
         - Добавление пользователя (identifier: username / email).
        """
        company = self.get_company_or_404(request)

        # Шаблон для сообщений
        success_message = None
        error_message = None

        # 1) Удаление пользователя
        remove_user_id = request.POST.get("remove_user_id")
        if remove_user_id:
            try:
                user_to_remove = User.objects.get(pk=remove_user_id)
                # Проверяем, что пользователь состоит в компании и не директор
                if (
                    user_to_remove in company.users.all()
                    and user_to_remove != company.director
                ):
                    company.users.remove(user_to_remove)
                    success_message = (
                        f"Пользователь {user_to_remove.username} удалён из компании."
                    )
                else:
                    error_message = "Невозможно удалить данного пользователя (он директор или не в компании)."
            except User.DoesNotExist:
                error_message = "Пользователь для удаления не найден."

        # 2) Добавление пользователя (по username или email)
        identifier = request.POST.get("identifier", "").strip()
        if identifier:
            try:
                user_to_add = User.objects.get(
                    Q(username=identifier) | Q(email=identifier)
                )
                # Добавляем, если он не директор и ещё не в списке
                if (
                    user_to_add != company.director
                    and user_to_add not in company.users.all()
                ):
                    company.users.add(user_to_add)
                    success_message = f"Пользователь {user_to_add.username} добавлен!"
                else:
                    error_message = (
                        "Пользователь уже в компании или является директором."
                    )
            except User.DoesNotExist:
                error_message = f"Пользователь '{identifier}' не найден."

        # Собираем заново страницу с пользователями
        page_obj = self.get_page_obj(request, company)

        context = {
            "company": company,
            "page_obj": page_obj,
            "search_query": request.GET.get("search", ""),
            "success": success_message,
            "error": error_message,
        }
        return render(request, self.template_name, context)

    # ------------------ Вспомогательные методы ------------------ #

    def get_company_or_404(self, request):
        """
        Возвращает первую доступную компанию,
        где текущий пользователь либо директор, либо в списке users.
        Иначе выбрасывает 404.
        """
        company_qs = Company.objects.filter(
            Q(director=request.user) | Q(users=request.user)
        ).distinct()
        if not company_qs.exists():
            raise Http404("Компания не найдена.")
        return company_qs.first()

    def get_page_obj(self, request, company):
        """
        Возвращает Page-объект (с пагинацией) по списку пользователей company.users,
        с учётом поля поиска ?search=...
        """
        user_list = company.users.all().order_by("id")
        search_query = request.GET.get("search", "").strip()
        if search_query:
            user_list = user_list.filter(
                Q(username__icontains=search_query) | Q(email__icontains=search_query)
            )
        paginator = Paginator(user_list, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        return page_obj


class PersonalGroupListView(ListView):
    """
    Отображаем список групп, относящихся к компаниям,
    в которых текущий пользователь либо директор, либо состоит в users.
    """

    model = PersonalGroups
    template_name = "site/useraccount/personal_groups_list.html"
    context_object_name = "groups"
    paginate_by = 1

    def get_queryset(self):
        # Получим все компании, к которым есть доступ у пользователя (директор или в users)
        company_qs = Company.objects.filter(
            Q(director=self.request.user) | Q(users=self.request.user)
        ).distinct()
        # Фильтруем группы по этим компаниям
        return PersonalGroups.objects.filter(company__in=company_qs).distinct()


class PersonalGroupCreateView(CreateView):
    model = PersonalGroups
    form_class = PersonalGroupForm
    template_name = "site/useraccount/personal_groups_form.html"
    success_url = reverse_lazy("useraccount:groups_list")  # <-- Здесь указываем имя URL

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Логика определения, какую компанию использовать:
        company_qs = Company.objects.filter(
            director=self.request.user
        )  # Или ваш фильтр
        if company_qs.count() == 1:
            kwargs["instance"] = PersonalGroups(company=company_qs.first())
        else:
            company_id = self.request.GET.get("company_id")
            if company_id:
                try:
                    chosen_company = company_qs.get(pk=company_id)
                    kwargs["instance"] = PersonalGroups(company=chosen_company)
                except Company.DoesNotExist:
                    pass
        return kwargs


class PersonalGroupUpdateView(UpdateView):
    model = PersonalGroups
    form_class = PersonalGroupForm
    template_name = "site/useraccount/personal_groups_form.html"

    def get_object(self, queryset=None):
        # Получаем объект стандартным способом
        obj = super().get_object(queryset)
        # Можно проверить, имеет ли текущий пользователь право на редактирование
        # (например, он директор компании или в списке Company.users)
        # Если нет - выбросить 404 или PermissionDenied
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Если нужно, можно передать company для дальнейшей проверки:
        # kwargs['company'] = obj.company
        return kwargs


@method_decorator(csrf_protect, name="dispatch")
class PersonalGroupAjaxDeleteView(View):
    """
    Удаляет PersonalGroups по AJAX-запросу POST.
    Возвращает JSON-ответ.
    """

    def post(self, request, pk):
        # Допустим, удалять может только директор или пользователь в списке company.
        # Настроим фильтр (Q) по доступным компаниям:
        company_qs = Company.objects.filter(
            Q(director=request.user) | Q(users=request.user)
        ).distinct()

        # Пробуем получить группу из этих компаний
        group = get_object_or_404(PersonalGroups, pk=pk, company__in=company_qs)

        # Удаляем
        group.delete()

        # Возвращаем JSON c кодом 200 и сообщением об успехе
        return JsonResponse({"message": "deleted"}, status=200)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class WithdrawPage(LoginRequiredMixin, TemplateView):
    template_name = "site/useraccount/withdraw_payment.html"
    model = Withdrawal
    context_object_name = "withdraw"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        withdraw = Withdrawal.objects.filter(user=user).filter(type=0).order_by("-pk")

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            withdraw = withdraw.filter(pk=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            withdraw = withdraw.filter(type=search_type)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                withdraw = withdraw.filter(create=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(withdraw, 10)
        page = self.request.GET.get("page")
        try:
            withdraw_list = paginator.page(page)
        except PageNotAnInteger:
            withdraw_list = paginator.page(1)
        except EmptyPage:
            withdraw_list = paginator.page(paginator.num_pages)

        context["withdraw_list"] = withdraw_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = withdraw_list
        context["types"] = Withdrawal.TYPE_CHOICES
        context["balance"] = user.balance
        context["frozen"] = user.frozen
        context["cards"] = user.cardowner.first()
        # Добавляем форму вывода
        context["withdraw_form"] = WithdrawForm()
        # Добавляем форму
        context["cards_form"] = CardsForm()
        # Форма для редактирования карты (если карта существует)
        if context["cards"]:
            context["edit_cards_form"] = CardsForm(instance=context["cards"])

        return context


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class WithdrawPagePoint(LoginRequiredMixin, TemplateView):
    template_name = "site/useraccount/withdraw_point.html"
    model = Withdrawal
    context_object_name = "withdraw"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        withdraw = Withdrawal.objects.filter(user=user).filter(type=1).order_by("-pk")

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            withdraw = withdraw.filter(pk=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            withdraw = withdraw.filter(type=search_type)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                withdraw = withdraw.filter(create=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(withdraw, 10)
        page = self.request.GET.get("page")
        try:
            withdraw_list = paginator.page(page)
        except PageNotAnInteger:
            withdraw_list = paginator.page(1)
        except EmptyPage:
            withdraw_list = paginator.page(paginator.num_pages)

        context["withdraw_list"] = withdraw_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = withdraw_list
        context["types"] = Withdrawal.TYPE_CHOICES
        context["point"] = user.point
        context["frozen"] = user.frozen
        context["cards"] = user.cardowner.first()
        # Добавляем форму вывода
        context["withdraw_form"] = WithdrawForm()
        # Добавляем форму
        context["cards_form"] = CardsForm()
        # Форма для редактирования карты (если карта существует)
        if context["cards"]:
            context["edit_cards_form"] = CardsForm(instance=context["cards"])

        return context


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class WithdrawCreateView(CreateView):
    model = Withdrawal
    form_class = WithdrawForm

    def post(self, request, *args, **kwargs):
        # Создаем экземпляр формы с переданными данными
        form = self.form_class(data=request.POST, user=request.user)

        if form.is_valid():
            # Получаем сумму, которую пользователь хочет вывести
            amount = form.cleaned_data["amount"]

            # Получаем пользователя
            user = request.user

            # Проверка, что у пользователя достаточно средств
            if amount > user.balance:
                return JsonResponse(
                    {
                        "success": False,
                        "errors": f"Вы не можете списать больше {user.balance:.2f}.",
                    },
                    status=400,
                )

            # Обновляем баланс пользователя, списывая сумму
            user.balance -= amount
            user.save()

            # Сохраняем запрос на вывод
            withdrawal = form.save(commit=False)
            withdrawal.user = user  # Устанавливаем пользователя
            withdrawal.type_payment = 1  # Устанавливаем type_payment = 1 (Списание)
            withdrawal.type = 0  # Устанавливаем type = 0 (Деньги)
            withdrawal.save()

            return JsonResponse(
                {"success": True, "message": "Запрос на вывод успешно создан."},
                status=201,
            )
        else:
            # Если есть ошибки валидации, возвращаем их в читаемом виде
            error_message = " ".join(
                [
                    f"{field}: {', '.join(errors)}"
                    for field, errors in form.errors.items()
                ]
            )
            return JsonResponse({"success": False, "errors": error_message}, status=400)


@method_decorator(
    csrf_exempt, name="dispatch"
)  # Для защиты CSRF можно убрать в будущем, если запросы из тех же источников
@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class CardsCreateView(CreateView):
    model = Cards
    form_class = CardsForm
    success_url = reverse_lazy("useraccount:withdraw")

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            form.instance.user = self.request.user
            form.save()
            return JsonResponse(
                {"success": True, "message": "Карта успешно добавлена"}, status=201
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class CardsUpdateView(UpdateView):
    model = Cards
    form_class = CardsForm
    success_url = reverse_lazy("useraccount:withdraw")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.instance.user = self.request.user
            form.save()
            return JsonResponse(
                {"success": True, "message": "Карта успешно обновлена"}, status=200
            )
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
