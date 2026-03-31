from django.apps import apps
from django.core.mail import EmailMultiAlternatives
from django.db.models.functions import TruncDate, TruncHour
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST, require_http_methods
import uuid
from django.contrib.sites.models import Site
import xml.etree.ElementTree as ET
import xml.dom.minidom
import xml.etree.ElementTree as ET
import xml.dom.minidom
from django.http import HttpResponse, Http404
import csv
import io
import xlsxwriter
import requests
from django.core.files import File
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from django.utils.translation import get_language
import pprint
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage

import json
from django.utils.timezone import now, timedelta
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_protect
from django.http import (
    HttpResponseRedirect,
    HttpResponseBadRequest,
)
from datetime import datetime
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum, Avg
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout, get_user_model
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordResetDoneView,
)
from django.urls import reverse_lazy
from django.urls import reverse
from django.contrib import messages
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, UpdateView, DeleteView
from django.conf import settings
from documentation.models import Documentations, DocumentationsMedia
from payment.models import PaymentType
from useraccount.forms import (
    SignUpForm,
    UserProfileForm,
    PasswordResetEmailForm,
    SetPasswordFormCustom,
    CardsForm,
    SignUpClientForm,
)
from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction, models
from django.shortcuts import render
from webmain.models import (
    Blogs,
    CategorysBlogs,
    Pages,
    ContactPageInformation,
    TagsBlogs,
    Sponsorship,
    ExtendedSite,
    Gallery,
    Service,
    Price,
    ServiceMedia,
)
from moderation.forms import (
    LessonForm,
    SettingsModerationForm,
    AssetForm,
    SelectedProductFormSet,
    VacancyForm,
    CollaborationsForm,
    BlogsForm,
    ProductExpensePositionForm,
    ProductExpensePurchaseForm,
    PagesForm,
    SeoForm, ImportHistoryForm,
    NotificationForm,
    CategorysBlogsForm,
    PaymentTypeForm,
    DocumentationForm,
    ContactPageInformationForm,
    TagsBlogsForm,
    SponsorshipForm,
)
from webmain.models import (
    Seo,
    GalleryMedia,
    SettingsGlobale,
    HomePage,
    AboutPage,
    ContactPage,
    Faqs,
)
from moderation.forms import (
    ProductsForm,
    ProductsVariableFormSet,
    AtributeForm,
    OrderForm,
    GalleryForm,
    StatusPaymentForm,
    PriceForm,
    ServiceForm,
    ExtendedSiteForm,
    TicketCommentForm,
    ContactPageForm,
    SettingsGlobaleForm,
    AboutPageForm,
    FaqsForm,
    WithdrawForm,
    GroupForm,
    WorkerUpdateProfileForm,
    ComplaintForm,
    CategoriesForm,
)
from useraccount.models import Profile, Notification, Withdrawal, Cards
from moderation.models import (
    Asset,
    Maintenance,
    AssetUsage,
    Ticket,
    TicketComment,
    TicketCommentMedia,
    Notificationgroups,
    Groups,
    Collaborations,
)
import os
from hr.models import Schedule, WorkShift, Vacancy, VacancyResponse, HRChangeLog, Lesson, LessonMaterial, TestResult
from crm.models import StatusPayment, Task, Lead
from hr.forms import WorkShiftPhotoForm
from webmain.forms import SubscriptionForm
from shop.models import (ProductExpensePurchase, ManufacturersExpense, ManufacturersIncome,
                         StockAvailability,
                         ProductsVariable,
                         ProductsGallery,
                         Storage,
                         Atribute,
                         Variable,
                         ApplicationsProducts,
                         Complaint,
                         Valute,
                         Categories,
                         SelectedProduct,
                         Products,
                         Reviews,
                         Manufacturers,
                         FaqsProducts,
                         ImportHistory,
                         ProductComment,
                         )
from django.core.management import call_command
import subprocess  # альтернатива call_command
import shutil

from development.models import ThemesCastegorys, Themes, SettingsModeration

from useraccount.forms import CustomAuthenticationForm

from payment.models import Order

from shop.models import Tag, Brands, ProductExpense, ProductExpensePosition, ProductExpensePurchase

from moderation.models import AggregatedExpense

from shop.models import Cart

from moderation.forms import SendEmailForm, EmailTemplateForm, EmailTemplateFilterForm
from moderation.models import EmailLog, EmailQueue, EmailTemplate

from moderation.forms import QuickCallForm, CallSettingsForm, CallQueueForm, PhoneNumberForm, CallNoteForm, \
    CallFilterForm
from moderation.models import CallSettings, CallRecord, CallRecording, VoiceMenu, CallQueue, PhoneNumber

from moderation.forms import VoiceMenuForm

from moderation.forms import SyncProductsForm, AdditionalServiceForm, DeliverySettingsForm, MessengerSettingsForm, \
    PaymentSettingsForm, MarketplaceSettingsForm, IntegrationServiceForm
from moderation.models import IntegrationService, MessengerMessage, DeliveryOrder, PaymentTransaction, \
    MarketplaceOrder, MarketplaceProduct, IntegrationLog, AdditionalService, MessengerIntegration, DeliveryIntegration, \
    PaymentIntegration


class ModerationHome(View):
    template_name = "moderations/base.html"
    
    def get(self, request):
        return render(request, self.template_name)



class UserShiftListView(ListView):
    model = WorkShift
    template_name = "moderations/user_shift_list.html"
    context_object_name = "shifts"
    paginate_by = 25  # при желании

    def get_queryset(self):
        # пользователь из URL
        self.user_obj = get_object_or_404(Profile, pk=self.kwargs["user_id"])

        today = timezone.localdate()

        # смены, у которых дата начала/окончания сегодня или в прошлом
        # (если хотите учитывать только date_start — оставьте только первое условие)
        q = (
                Q(date_start__isnull=False, date_start__lte=today) |
                Q(date_end__isnull=False, date_end__lte=today)
        )

        return (
            WorkShift.objects
            .filter(user=self.user_obj)
            .filter(q)
            .order_by(
                "-date_start", "-time_start",  # сначала последние выходы
                "-date_end", "-time_end"
            )
            .select_related("user")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user_obj"] = self.user_obj
        return ctx


class WorkShiftUpdateView(View):
    def get(self, request):
        shift_id = request.GET.get('shift_id')

        if not shift_id:
            return JsonResponse({'status': 'error', 'message': 'shift_id не передан'}, status=400)

        try:
            shift = WorkShift.objects.get(id=shift_id)
            return JsonResponse({
                'status': 'success',
                'data': {
                    'work_status': shift.work_status,
                }
            })
        except WorkShift.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Смена не найдена'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def post(self, request):
        try:
            form_data = request.POST
            files = request.FILES

            shift_id = form_data.get('shift_id')
            if not shift_id:
                return JsonResponse({'status': 'error', 'message': 'shift_id не передан'}, status=400)

            try:
                shift = WorkShift.objects.get(id=shift_id)
            except WorkShift.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Смена не найдена'}, status=404)

            # Автоматически определяем тип смены из запроса
            work_status = form_data.get('work_status')
            if work_status:
                shift.work_status = work_status

            # Автоматически устанавливаем дату/время модерации
            shift.moderator = request.user
            shift.moderated_at = timezone.now()

            # Автоматически устанавливаем дату/время операции
            now = timezone.now()
            if shift.work_status == '1':  # Выход на смену
                shift.date_start = now.date()
                shift.time_start = now.time()

                # Обрабатываем файлы для выхода
                if 'photo_accept_place' in files:
                    shift.photo_accept_place = files['photo_accept_place']
                if 'photo_entry_place' in files:
                    shift.photo_entry_place = files['photo_entry_place']
                if 'selfie_entry' in files:
                    shift.selfie_entry = files['selfie_entry']
                if 'video_entry' in files:
                    shift.video_entry = files['video_entry']

            else:  # Уход со смены
                shift.date_end = now.date()
                shift.time_end = now.time()

                # Обрабатываем файлы для ухода
                if 'photo_handover_place' in files:
                    shift.photo_handover_place = files['photo_handover_place']
                if 'photo_exit_place' in files:
                    shift.photo_exit_place = files['photo_exit_place']
                if 'selfie_exit' in files:
                    shift.selfie_exit = files['selfie_exit']
                if 'video_exit' in files:
                    shift.video_exit = files['video_exit']

            shift.save()
            return JsonResponse({'status': 'success', 'message': 'Смена обновлена'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


LANGUAGE_FILE = os.path.join(settings.BASE_DIR, "_project", "settings", "language.py")


def read_languages():
    local_vars = {}
    with open(LANGUAGE_FILE, "r", encoding="utf-8") as f:
        code = compile(f.read(), LANGUAGE_FILE, "exec")
        exec(code, {}, local_vars)
    return local_vars.get("LANGUAGES", [])


def write_languages_and_info(languages):
    lines = []
    lines.append("from django.utils.translation import gettext_lazy as _\n")
    lines.append("LANGUAGES = [")
    for code, name in languages:
        lines.append(f"    ('{code}', _('{name}')),")
    lines.append("]\n")

    lines.append("from django.conf.locale import LANG_INFO")
    lines.append("LANG_INFO.update({")
    for code, name in languages:
        lines.append(f"    '{code}': {{")
        lines.append("        'bidi': False,")
        lines.append(f"        'code': '{code}',")
        lines.append(f"        'name': '{name}',")
        lines.append(f"        'name_local': '{name}',")
        lines.append("    },")
    lines.append("})\n")

    with open(LANGUAGE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class LanguageListView(View):
    def get(self, request):
        languages = read_languages()
        return render(
            request, "moderations/language_list.html", {"languages": languages}
        )

    def post(self, request):
        action = request.POST.get("action")
        code = request.POST.get("code", "").lower().strip()
        name = request.POST.get("name", "").strip()
        languages = read_languages()

        if action == "add":
            if not code or not name:
                return HttpResponseBadRequest("Code and Name are required.")
            if not any(code == lang[0] for lang in languages):
                languages.append((code, name))
                write_languages_and_info(languages)

                # ⏩ Добавляем язык в LANGUAGES в рантайме
                if (code, name) not in settings.LANGUAGES:
                    settings.LANGUAGES += [(code, name)]

                # 🗂️ Создаём директорию перевода
                locale_dir = os.path.join(
                    settings.BASE_DIR, "locale", code, "LC_MESSAGES"
                )
                os.makedirs(locale_dir, exist_ok=True)

                try:
                    en_po = os.path.join(
                        settings.BASE_DIR, "locale", "en", "LC_MESSAGES", "django.po"
                    )
                    new_po = os.path.join(locale_dir, "django.po")

                    if os.path.exists(en_po):
                        shutil.copyfile(en_po, new_po)

                        # ✅ Очистка всех msgstr после копирования
                        with open(new_po, "r", encoding="utf-8") as f:
                            lines = f.readlines()

                        new_lines = []
                        in_msgstr = False
                        for line in lines:
                            if line.startswith("msgstr"):
                                in_msgstr = True
                                new_lines.append('msgstr ""\n')
                            elif in_msgstr and line.startswith('"'):
                                continue  # Удаляем содержимое msgstr
                            else:
                                in_msgstr = False
                                new_lines.append(line)

                        with open(new_po, "w", encoding="utf-8") as f:
                            f.writelines(new_lines)
                    else:
                        call_command("makemessages", locale=[code], verbosity=1)

                    # ✅ Компиляция переводов
                    call_command("compilemessages", locale=[code], verbosity=1)

                    # 🛠️ Генерация и применение миграций
                    call_command("makemigrations")
                    call_command("migrate")

                    # 🔄 Перезапуск Gunicorn (если используется)
                    subprocess.run(["systemctl", "restart", "gunicorn"], check=True)

                    messages.success(
                        request,
                        f"Язык '{name}' добавлен, перевод создан и миграции выполнены.",
                    )
                except Exception as e:
                    messages.warning(request, f"Язык добавлен, но возникла ошибка: {e}")

            return redirect("moderation:language_list")

        elif action == "delete":
            if not code:
                return HttpResponseBadRequest("Code is required.")
            languages = [lang for lang in languages if lang[0] != code]
            write_languages_and_info(languages)
            messages.success(request, f"Язык '{code}' удалён.")
            return redirect("moderation:language_list")

        return HttpResponseBadRequest("Неизвестное действие.")


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class LanguageEditView(View):
    def get(self, request, code):
        po_path = os.path.join(
            settings.BASE_DIR, "locale", code, "LC_MESSAGES", "django.po"
        )

        if not os.path.exists(po_path):
            return HttpResponseBadRequest(
                f"Файл перевода для языка '{code}' не найден."
            )

        with open(po_path, "r", encoding="utf-8") as f:
            content = f.read()

        return render(
            request,
            "moderations/language_edit.html",
            {
                "code": code,
                "content": content,
            },
        )

    def post(self, request, code):
        po_path = os.path.join(
            settings.BASE_DIR, "locale", code, "LC_MESSAGES", "django.po"
        )

        if not os.path.exists(po_path):
            return HttpResponseBadRequest(
                f"Файл перевода для языка '{code}' не найден."
            )

        content = request.POST.get("content", "")
        if not content:
            messages.error(request, "Файл перевода не может быть пустым.")
            return redirect("moderation:language_edit", code=code)

        with open(po_path, "w", encoding="utf-8") as f:
            f.write(content)

        # После сохранения можно скомпилировать .mo
        try:
            from django.core.management import call_command

            call_command("compilemessages", locale=[code])
            messages.success(
                request, f"Файл перевода для '{code}' успешно сохранён и скомпилирован."
            )
        except Exception as e:
            messages.warning(
                request, f"Файл сохранён, но не удалось скомпилировать: {e}"
            )

        return redirect("moderation:language_edit", code=code)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class DashbordView(TemplateView):
    template_name = "moderations/dashbord.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Текущая дата
        now = timezone.now()

        # Начало и конец месяца
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            end_month = now.replace(month=now.month + 1, day=1)

        # Агрегация только за текущий месяц и со статусом 'passed'
        sums = Lead.objects.filter(
            status="passed", created_at__gte=start_month, created_at__lt=end_month
        ).aggregate(
            total_amount=Sum("amount"),
            total_profit=Sum("profit"),
            total_expenditure=Sum("expenditure"),
        )

        context.update(sums)
        context["payments"] = StatusPayment.objects.order_by("-id")[:7]
        context["manufacturers"] = Manufacturers.objects.order_by("-id").all
        context["tickets"] = Ticket.objects.filter(status=0).order_by("-date")[:3]
        context["total_categories"] = Categories.objects.count()
        context["total_storage"] = Storage.objects.count()
        context["total_manufacturers"] = Manufacturers.objects.count()
        context["total_products"] = Products.objects.count()
        context["total_valute"] = Valute.objects.count()
        context["total_reviews"] = Reviews.objects.count()
        context["total_faq"] = FaqsProducts.objects.count()
        context["total_variable"] = Variable.objects.count()
        context["total_comment"] = ProductComment.objects.count()
        context["total_complaint"] = Complaint.objects.count()
        context["total_applications"] = ApplicationsProducts.objects.count()
        context["total_order_cool"] = Order.objects.filter(type=2).count()
        context["total_order"] = Order.objects.count()
        return context


class CustomLoginView(auth_views.LoginView):
    template_name = "moderations/login.html"
    form_class = CustomAuthenticationForm

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def dispatch(self, request, *args, **kwargs):
        """Запрещаем авторизованному пользователю заходить на страницу логина"""
        if request.user.is_authenticated:
            return redirect(self.get_authenticated_redirect_url())  # Редирект в профиль

        return super().dispatch(request, *args, **kwargs)

    def get_authenticated_redirect_url(self):
        """Определяет URL для редиректа авторизованного пользователя"""
        user_type = self.request.user.type
        return (
            reverse("moderation:edit_profile")
            if user_type == 0
            else reverse("useraccount:edit_profile")
        )

    def get_success_url(self):
        """Определяет, куда перенаправить пользователя после входа"""
        next_url = self.request.GET.get("next")

        # Проверяем, чтобы next не указывал на страницу логина (во избежание бесконечного цикла)
        if next_url and "login" not in next_url:
            return next_url

        return (
            self.get_authenticated_redirect_url()
        )  # Если next некорректный, ведем в профиль

    def form_invalid(self, form):
        # Обрабатываем неуспешную аутентификацию
        return self.render_to_response(self.get_context_data(form=form))


def subscribe(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Спасибо за подписку!")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        else:
            messages.error(request, "Вы уже подписаны на рассылку!")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class IndevelopmentView(TemplateView):
    template_name = "moderations/_indevelopment.html"


"""Регистрация/Авторизация"""


def custom_logout(request):
    logout(request)
    return redirect("webmain:login")


class CustomPasswordResetView(PasswordResetView):
    template_name = "moderations/restore_access.html"
    email_template_name = "moderations/email/password_reset_email.html"
    subject_template_name = "moderations/email/password_reset_subject.txt"
    form_class = PasswordResetEmailForm
    success_url = reverse_lazy("webmain:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "moderations/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "moderations/restore_access_user.html"
    form_class = SetPasswordFormCustom
    success_url = reverse_lazy("webmain:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "moderations/password_reset_complete.html"


"""Личный кабинет"""


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EditMyProfileView(TemplateView, LoginRequiredMixin):
    template_name = "moderations/profile_edit.html"

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
        password_form = PasswordChangeForm(
            data=request.POST, user=request.user
        )  # Форма для смены пароля

        # Обработка данных профиля
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлен успешно.")
        else:
            messages.error(request, "Ошибка при обновлении профиля.")
            print("Form errors:", form.errors)

        # Обработка смены пароля
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(
                request, user
            )  # Чтобы пользователь не вышел после смены пароля
            messages.success(request, "Пароль изменен успешно.")
        else:
            messages.error(request, "Ошибка при смене пароля.")
            print("Password form errors:", password_form.errors)

        context = self.get_context_data(
            form=form, password_form=password_form, title="Личные данные"
        )
        return self.render_to_response(context)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class GroupListView(ListView):
    """
    Отображаем список групп, относящихся к компаниям,
    в которых текущий пользователь либо директор, либо состоит в users.
    """

    model = Groups
    template_name = "moderations/personal_groups_list.html"
    context_object_name = "groups"
    paginate_by = 1


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class GroupCreateView(CreateView):
    model = Groups
    form_class = GroupForm
    template_name = "moderations/personal_groups_form.html"
    success_url = reverse_lazy("moderation:groups_list")  # <-- Здесь указываем имя URL


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class GroupUpdateView(UpdateView):
    model = Groups
    form_class = GroupForm
    template_name = "moderations/personal_groups_form.html"
    success_url = reverse_lazy("moderation:groups_list")  # <-- Здесь указываем имя URL


@method_decorator(csrf_protect, name="dispatch")
class GroupAjaxDeleteView(View):
    """
    Удаляет PersonalGroups по AJAX-запросу POST.
    Возвращает JSON-ответ.
    """

    def post(self, request, pk):
        # Допустим, удалять может только директор или пользователь в списке company.

        # Пробуем получить группу из этих компаний
        group = get_object_or_404(Groups, pk=pk)

        # Удаляем
        group.delete()

        # Возвращаем JSON c кодом 200 и сообщением об успехе
        return JsonResponse({"message": "deleted"}, status=200)


@method_decorator(login_required(login_url="useraccount:edit_profile"), name="dispatch")
class UserListView(ListView):
    model = Profile
    template_name = "moderations/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        name_query = self.request.GET.get("q")
        contract_query = self.request.GET.get("contract")

        queryset = (
            Profile.objects.filter(Q(type=1))
            .exclude(id=self.request.user.id)
            .order_by("id")
        )

        if name_query:
            queryset = queryset.filter(
                Q(first_name__iregex=name_query)
                | Q(last_name__iregex=name_query)
                | Q(middle_name__iregex=name_query)
            )

        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "moderations/users_list_partial.html", context, request=self.request
            )
            return JsonResponse({"html": html})
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = Profile.objects.filter(
            type=1
        ).count()  # Общее количество пользователей
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SettingGlobalUpdateView(LoginRequiredMixin, UpdateView):
    model = SettingsGlobale
    form_class = SettingsGlobaleForm
    template_name = "moderations/settings_global.html"
    context_object_name = "site"
    success_url = reverse_lazy("moderation:settings_global")

    def get_object(self, queryset=None):
        return get_object_or_404(SettingsGlobale, pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        homepage = self.get_object()

        if homepage.jsontemplate:
            try:
                context["jsontemplate"] = json.loads(homepage.jsontemplate)
            except json.JSONDecodeError:
                context["jsontemplate"] = {}
        else:
            context["jsontemplate"] = {}

        model_data = {
            "blogs": Blogs.objects.all(),
            "services": Service.objects.all(),
            "gallery": Gallery.objects.all(),
            "faqs": Faqs.objects.all(),
            "sponsorship": Sponsorship.objects.all(),
            "products": Products.objects.all(),
        }
        context["model_data"] = model_data

        return context

    def form_valid(self, form):
        json_data = self.request.POST.get("json_data", None)
        print(
            "Received json_data:", json_data
        )  # Для отладки, убедитесь, что данные получены

        if json_data:
            try:
                jsontemplate = json.loads(json_data)

                formatted_json = {"page": "settings", "fields": {}}

                # Директория для сохранения файлов
                upload_dir = os.path.join(settings.MEDIA_ROOT, "jsontemplate")
                os.makedirs(
                    upload_dir, exist_ok=True
                )  # Создаем папку, если она не существует

                # Загружаем старые данные только для "type": "media"
                about = form.instance
                old_data = (
                    json.loads(about.jsontemplate)
                    if about.jsontemplate
                    else [{"fields": {}}]
                )
                old_fields = old_data[0].get("fields", {})

                # Проходим по блокам и обрабатываем новые данные
                for block in jsontemplate:
                    for key, value in block.items():
                        new_key = value.get("key", key)

                        # Проверяем, если type == "media", то загружаем старые данные для файлов
                        if value.get("type") == "media":
                            # Проверка на наличие файла для обновления
                            uploaded_file = self.request.FILES.get(f"{new_key}_file")

                            if uploaded_file:
                                # Если файл загружается, сохраняем его в MEDIA/jsontemplate
                                file_path = os.path.join(upload_dir, uploaded_file.name)
                                with open(file_path, "wb+") as destination:
                                    for chunk in uploaded_file.chunks():
                                        destination.write(chunk)

                                # Сохраняем относительный путь к файлу
                                value["info"] = (
                                    f"/_media/jsontemplate/{uploaded_file.name}"
                                )

                            else:
                                # Если файла нет, проверяем старое значение для файла
                                if new_key in old_fields:
                                    # Берем старое значение info, если оно существует
                                    value["info"] = old_fields.get(new_key, {}).get(
                                        "info", value.get("info", "")
                                    )
                                else:
                                    # Если старое значение не существует, оставляем новое
                                    value["info"] = value.get("info", "")

                        # Преобразование строки в список, если это необходимо
                        if (
                                isinstance(value["info"], str)
                                and value["info"].startswith("[")
                                and value["info"].endswith("]")
                        ):
                            try:
                                value["info"] = json.loads(value["info"])
                            except json.JSONDecodeError:
                                pass

                        elif isinstance(value["info"], list):
                            value["info"] = [
                                int(item)
                                if isinstance(item, str) and item.isdigit()
                                else item
                                for item in value["info"]
                            ]

                        # Применяем изменения и сохраняем только измененные данные
                        formatted_json["fields"][new_key] = {
                            "field": value["field"],
                            "info": value["info"],
                            "type": value.get("type", "information"),
                        }

                # Сохраняем обновленный jsontemplate
                homepage = form.save(commit=False)
                # Здесь мы записываем новое значение jsontemplate в модель
                homepage.jsontemplate = json.dumps(
                    [formatted_json], ensure_ascii=False, indent=2
                )

                print("Updated jsontemplate:", homepage.jsontemplate)

                homepage.save()

                print(
                    "homepage jsontemplate saved:", homepage.jsontemplate
                )  # Проверка сохранения
                return JsonResponse({"success": True})

            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Неверный формат JSON"})

        print("Form is valid. Form data:", form.cleaned_data)  # Проверка данных формы
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class HomepageUpdateView(UpdateView):
    model = HomePage
    template_name = "moderations/homepagesetform.html"
    context_object_name = "homepage"
    fields = [f.name for f in HomePage._meta.fields if f.name != "site"]

    def get_object(self, queryset=None):
        return get_object_or_404(HomePage, pk=self.kwargs.get("pk"))

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # ✅ Присваиваем site в экземпляре ДО валидации
        form.instance.site = self.get_object().site
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        homepage = self.get_object()

        if homepage.jsontemplate:
            try:
                context["jsontemplate"] = json.loads(homepage.jsontemplate)
            except json.JSONDecodeError:
                context["jsontemplate"] = {}
        else:
            context["jsontemplate"] = {}

        model_data = {
            "blogs": Blogs.objects.all(),
            "services": Service.objects.all(),
            "gallery": Gallery.objects.all(),
            "faqs": Faqs.objects.all(),
            "sponsorship": Sponsorship.objects.all(),
            "products": Products.objects.all(),
            "vendors": Manufacturers.objects.all(),
        }
        context["model_data"] = model_data

        return context

    def form_valid(self, form):
        json_data = self.request.POST.get("json_data", None)

        homepage = form.save(commit=False)  # site уже подставлен в get_form()

        if json_data:
            try:
                jsontemplate = json.loads(json_data)
                formatted_json = {"page": "home", "fields": {}}
                upload_dir = os.path.join(settings.MEDIA_ROOT, "jsontemplate")
                os.makedirs(upload_dir, exist_ok=True)

                old_data = (
                    json.loads(homepage.jsontemplate)
                    if homepage.jsontemplate
                    else [{"fields": {}}]
                )
                old_fields = old_data[0].get("fields", {})

                for block in jsontemplate:
                    for key, value in block.items():
                        new_key = value.get("key", key)

                        if value.get("type") == "media":
                            uploaded_file = self.request.FILES.get(f"{new_key}_file")
                            if uploaded_file:
                                file_path = os.path.join(upload_dir, uploaded_file.name)
                                with open(file_path, "wb+") as destination:
                                    for chunk in uploaded_file.chunks():
                                        destination.write(chunk)
                                value["info"] = (
                                    f"/_media/jsontemplate/{uploaded_file.name}"
                                )
                            else:
                                if new_key in old_fields:
                                    value["info"] = old_fields.get(new_key, {}).get(
                                        "info", value.get("info", "")
                                    )
                                else:
                                    value["info"] = value.get("info", "")

                        if (
                                isinstance(value["info"], str)
                                and value["info"].startswith("[")
                                and value["info"].endswith("]")
                        ):
                            try:
                                value["info"] = json.loads(value["info"])
                            except json.JSONDecodeError:
                                pass
                        elif isinstance(value["info"], list):
                            value["info"] = [
                                int(item)
                                if isinstance(item, str) and item.isdigit()
                                else item
                                for item in value["info"]
                            ]

                        formatted_json["fields"][new_key] = {
                            "field": value["field"],
                            "info": value["info"],
                            "type": value.get("type", "information"),
                        }

                homepage.jsontemplate = json.dumps(
                    [formatted_json], ensure_ascii=False, indent=2
                )

            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Неверный формат JSON"})

        homepage.save()
        return JsonResponse({"success": True})

    def form_invalid(self, form):
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class AboutUpdateView(LoginRequiredMixin, UpdateView):
    model = AboutPage
    form_class = AboutPageForm  # <-- Используется form_class
    template_name = "moderations/aboutform.html"
    context_object_name = "about"

    def get_object(self, queryset=None):
        return get_object_or_404(AboutPage, pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        about = self.get_object()

        if about.jsontemplate:
            try:
                context["jsontemplate"] = json.loads(about.jsontemplate)
            except json.JSONDecodeError:
                context["jsontemplate"] = {}
        else:
            context["jsontemplate"] = {}

        model_data = {
            "blogs": Blogs.objects.all(),
            "services": Service.objects.all(),
            "gallery": Gallery.objects.all(),
            "faqs": Faqs.objects.all(),
            "sponsorship": Sponsorship.objects.all(),
            "products": Products.objects.all(),
        }
        context["model_data"] = model_data

        return context

    def form_valid(self, form):
        json_data = self.request.POST.get("json_data", None)
        print(
            "Received json_data:", json_data
        )  # Для отладки, убедитесь, что данные получены

        if json_data:
            try:
                jsontemplate = json.loads(json_data)

                formatted_json = {"page": "home", "fields": {}}

                # Директория для сохранения файлов
                upload_dir = os.path.join(settings.MEDIA_ROOT, "jsontemplate")
                os.makedirs(
                    upload_dir, exist_ok=True
                )  # Создаем папку, если она не существует

                # Загружаем старые данные только для "type": "media"
                about = form.instance
                old_data = (
                    json.loads(about.jsontemplate)
                    if about.jsontemplate
                    else [{"fields": {}}]
                )
                old_fields = old_data[0].get("fields", {})

                # Проходим по блокам и обрабатываем новые данные
                for block in jsontemplate:
                    for key, value in block.items():
                        new_key = value.get("key", key)

                        # Проверяем, если type == "media", то загружаем старые данные для файлов
                        if value.get("type") == "media":
                            # Проверка на наличие файла для обновления
                            uploaded_file = self.request.FILES.get(f"{new_key}_file")

                            if uploaded_file:
                                # Если файл загружается, сохраняем его в MEDIA/jsontemplate
                                file_path = os.path.join(upload_dir, uploaded_file.name)
                                with open(file_path, "wb+") as destination:
                                    for chunk in uploaded_file.chunks():
                                        destination.write(chunk)

                                # Сохраняем относительный путь к файлу
                                value["info"] = (
                                    f"/_media/jsontemplate/{uploaded_file.name}"
                                )

                            else:
                                # Если файла нет, проверяем старое значение для файла
                                if new_key in old_fields:
                                    # Берем старое значение info, если оно существует
                                    value["info"] = old_fields.get(new_key, {}).get(
                                        "info", value.get("info", "")
                                    )
                                else:
                                    # Если старое значение не существует, оставляем новое
                                    value["info"] = value.get("info", "")

                        # Преобразование строки в список, если это необходимо
                        if (
                                isinstance(value["info"], str)
                                and value["info"].startswith("[")
                                and value["info"].endswith("]")
                        ):
                            try:
                                value["info"] = json.loads(value["info"])
                            except json.JSONDecodeError:
                                pass

                        elif isinstance(value["info"], list):
                            value["info"] = [
                                int(item)
                                if isinstance(item, str) and item.isdigit()
                                else item
                                for item in value["info"]
                            ]

                        # Применяем изменения и сохраняем только измененные данные
                        formatted_json["fields"][new_key] = {
                            "field": value["field"],
                            "info": value["info"],
                            "type": value.get("type", "information"),
                        }

                # Сохраняем обновленный jsontemplate
                contactpage = form.save(commit=False)
                # Здесь мы записываем новое значение jsontemplate в модель
                contactpage.jsontemplate = json.dumps(
                    [formatted_json], ensure_ascii=False, indent=2
                )

                print("Updated jsontemplate:", contactpage.jsontemplate)

                contactpage.save()

                print(
                    "contactpage jsontemplate saved:", contactpage.jsontemplate
                )  # Проверка сохранения
                return JsonResponse({"success": True})

            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Неверный формат JSON"})

        print("Form is valid. Form data:", form.cleaned_data)  # Проверка данных формы
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("moderation:about_update")


@method_decorator(csrf_exempt, name="dispatch")
class ContactPageInformationCreateView(View):
    def post(self, request, *args, **kwargs):
        contact_page = get_object_or_404(ContactPage, pk=kwargs.get("contact_page_id"))
        form = ContactPageInformationForm(request.POST, request.FILES)

        if form.is_valid():
            contact_info = form.save(commit=False)
            contact_info.contact_pages = contact_page
            contact_info.save()
            return JsonResponse(
                {
                    "success": True,
                    "id": contact_info.id,
                    "title_contact": contact_info.title_contact,
                    "description_contact": contact_info.description_contact,
                }
            )
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class ContactPageInformationUpdateView(View):
    def post(self, request, *args, **kwargs):
        contact_info = get_object_or_404(
            ContactPageInformation, pk=kwargs.get("contact_info_id")
        )
        form = ContactPageInformationForm(
            request.POST, request.FILES, instance=contact_info
        )

        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class ContactPageInformationDeleteView(View):
    def post(self, request, *args, **kwargs):
        contact_info = get_object_or_404(
            ContactPageInformation, pk=kwargs.get("contact_info_id")
        )
        contact_info.delete()
        return JsonResponse({"success": True})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = ContactPage
    form_class = ContactPageForm
    template_name = "moderations/contactpageform.html"
    context_object_name = "contactpage"

    def get_object(self, queryset=None):
        return get_object_or_404(ContactPage, pk=self.kwargs.get("pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contactpage = self.get_object()

        if contactpage.jsontemplate:
            try:
                context["jsontemplate"] = json.loads(contactpage.jsontemplate)
            except json.JSONDecodeError:
                context["jsontemplate"] = {}
        else:
            context["jsontemplate"] = {}

        # Загружаем ContactPageInformation
        context["contact_info"] = ContactPageInformation.objects.all()

        model_data = {
            "blogs": Blogs.objects.all(),
            "advertisement": Products.objects.all(),
        }
        context["model_data"] = model_data

        return context

    def form_valid(self, form):
        json_data = self.request.POST.get("json_data", None)
        print(
            "Received json_data:", json_data
        )  # Для отладки, убедитесь, что данные получены

        if json_data:
            try:
                jsontemplate = json.loads(json_data)

                formatted_json = {"page": "home", "fields": {}}

                # Директория для сохранения файлов
                upload_dir = os.path.join(settings.MEDIA_ROOT, "jsontemplate")
                os.makedirs(
                    upload_dir, exist_ok=True
                )  # Создаем папку, если она не существует

                # Загружаем старые данные только для "type": "media"
                contactpage = form.instance
                old_data = (
                    json.loads(contactpage.jsontemplate)
                    if contactpage.jsontemplate
                    else [{"fields": {}}]
                )
                old_fields = old_data[0].get("fields", {})

                # Проходим по блокам и обрабатываем новые данные
                for block in jsontemplate:
                    for key, value in block.items():
                        new_key = value.get("key", key)

                        # Проверяем, если type == "media", то загружаем старые данные для файлов
                        if value.get("type") == "media":
                            # Проверка на наличие файла для обновления
                            uploaded_file = self.request.FILES.get(f"{new_key}_file")

                            if uploaded_file:
                                # Если файл загружается, сохраняем его в MEDIA/jsontemplate
                                file_path = os.path.join(upload_dir, uploaded_file.name)
                                with open(file_path, "wb+") as destination:
                                    for chunk in uploaded_file.chunks():
                                        destination.write(chunk)

                                # Сохраняем относительный путь к файлу
                                value["info"] = (
                                    f"/_media/jsontemplate/{uploaded_file.name}"
                                )

                            else:
                                # Если файла нет, проверяем старое значение для файла
                                if new_key in old_fields:
                                    # Берем старое значение info, если оно существует
                                    value["info"] = old_fields.get(new_key, {}).get(
                                        "info", value.get("info", "")
                                    )
                                else:
                                    # Если старое значение не существует, оставляем новое
                                    value["info"] = value.get("info", "")

                        # Преобразование строки в список, если это необходимо
                        if (
                                isinstance(value["info"], str)
                                and value["info"].startswith("[")
                                and value["info"].endswith("]")
                        ):
                            try:
                                value["info"] = json.loads(value["info"])
                            except json.JSONDecodeError:
                                pass

                        elif isinstance(value["info"], list):
                            value["info"] = [
                                int(item)
                                if isinstance(item, str) and item.isdigit()
                                else item
                                for item in value["info"]
                            ]

                        # Применяем изменения и сохраняем только измененные данные
                        formatted_json["fields"][new_key] = {
                            "field": value["field"],
                            "info": value["info"],
                            "type": value.get("type", "information"),
                        }

                # Сохраняем обновленный jsontemplate
                contactpage = form.save(commit=False)
                # Здесь мы записываем новое значение jsontemplate в модель
                contactpage.jsontemplate = json.dumps(
                    [formatted_json], ensure_ascii=False, indent=2
                )

                print("Updated jsontemplate:", contactpage.jsontemplate)

                contactpage.save()

                print(
                    "Homepage jsontemplate saved:", contactpage.jsontemplate
                )  # Проверка сохранения
                return JsonResponse({"success": True})

            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Неверный формат JSON"})

        print("Form is valid. Form data:", form.cleaned_data)  # Проверка данных формы
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("moderation:contact_update")


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/faqs_settings.html"
    model = Faqs
    context_object_name = "faqs_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faq = Faqs.objects.order_by("-create").all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            faq = faq.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            faq = faq.filter(question__icontains=search_name)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                faq = faq.filter(create__date=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(faq, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqCreateView(LoginRequiredMixin, CreateView):
    model = Faqs
    form_class = FaqsForm
    template_name = "moderations/faqs_form.html"
    success_url = reverse_lazy("moderation:faq_settings")
    context_object_name = "faqs"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqUpdateView(LoginRequiredMixin, UpdateView):
    model = Faqs
    form_class = FaqsForm
    template_name = "moderations/faqs_form.html"
    success_url = reverse_lazy("moderation:faq_settings")
    context_object_name = "faqs"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:faq_settings")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            Faqs.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class BlogsSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/blogs_settings.html"
    model = Blogs
    context_object_name = "blogs_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blogs = Blogs.objects.all().order_by("-create")
        context["categories"] = CategorysBlogs.objects.all()

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            blogs = blogs.filter(name__icontains=search_name)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                blogs = blogs.filter(create__date=search_date)
            except ValueError:
                pass

        search_category = self.request.GET.get("search_category", "")
        if search_category:
            blogs = blogs.filter(category__id=search_category)

        # Пагинация
        paginator = Paginator(blogs, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            blogs_list = paginator.page(page)
        except PageNotAnInteger:
            blogs_list = paginator.page(1)
        except EmptyPage:
            blogs_list = paginator.page(paginator.num_pages)

        context["blogs_list"] = blogs_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = blogs_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class GallerySettings(LoginRequiredMixin, ListView):
    template_name = "moderations/gallery_settings.html"
    model = Gallery
    context_object_name = "gallery_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gallery = Gallery.objects.all().order_by("-create")

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            gallery = gallery.filter(name__icontains=search_name)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                gallery = gallery.filter(create__date=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(gallery, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            gallery_list = paginator.page(page)
        except PageNotAnInteger:
            gallery_list = paginator.page(1)
        except EmptyPage:
            gallery_list = paginator.page(paginator.num_pages)

        context["gallery_list"] = gallery_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = gallery_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class GalleryCreateView(LoginRequiredMixin, CreateView):
    model = Gallery
    form_class = GalleryForm
    template_name = "moderations/gallery_form.html"
    success_url = reverse_lazy("moderation:gallery_settings")
    context_object_name = "gallery"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = CategorysBlogs.objects.all()
        if self.object:
            context["existing_files"] = self.object.gallerymedia_set.all()
        return context

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        gallery = form.save(commit=False)

        # Обработка удаления обложки (cover)
        if self.request.POST.get("delete_cover") == "true":
            if gallery.cover:
                gallery.cover.delete()  # Удаляем файл из хранилища
                gallery.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if gallery.previev:
                gallery.previev.delete()
                gallery.previev = None

        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            GalleryMedia.objects.filter(
                id__in=delete_files_ids.split(","), gallery=gallery
            ).delete()

        # Сохраняем галерею
        gallery.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        files = self.request.FILES.getlist("files")
        for file in files:
            GalleryMedia.objects.create(gallery=gallery, file=file)

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class GalleryUpdateView(LoginRequiredMixin, UpdateView):
    model = Gallery
    form_class = GalleryForm
    template_name = "moderations/gallery_form.html"
    success_url = reverse_lazy("moderation:gallery_settings")
    context_object_name = "gallery"

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        gallery = form.save(commit=False)

        # Обработка удаления обложки (cover)
        if self.request.POST.get("delete_cover") == "true":
            if gallery.cover:
                gallery.cover.delete()  # Удаляем файл из хранилища
                gallery.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if gallery.previev:
                gallery.previev.delete()
                gallery.previev = None

        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            GalleryMedia.objects.filter(
                id__in=delete_files_ids.split(","), gallery=gallery
            ).delete()

        # Сохраняем изменения
        gallery.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        files = self.request.FILES.getlist("files")
        for file in files:
            GalleryMedia.objects.create(gallery=gallery, file=file)

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Для отладки
        messages.error(self.request, "Ошибка сохранения. Проверьте форму")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.object:
            context["existing_files"] = self.object.gallerymedia_set.all()

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ServicesSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/service_settings.html"
    model = Service
    context_object_name = "service_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = Service.objects.all().order_by("-create")

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            service = service.filter(name__icontains=search_name)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                service = service.filter(create__date=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(service, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            service_list = paginator.page(page)
        except PageNotAnInteger:
            service_list = paginator.page(1)
        except EmptyPage:
            service_list = paginator.page(paginator.num_pages)

        context["service_list"] = service_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = service_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ServicesCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = "moderations/service_form.html"
    success_url = reverse_lazy("moderation:service_settings")
    context_object_name = "services"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = CategorysBlogs.objects.all()

        if self.object:
            context["existing_files"] = self.object.servicemedia_set.all()

        return context

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        services = form.save(commit=False)

        # Обработка удаления обложки (cover)
        if self.request.POST.get("delete_cover") == "true":
            if services.cover:
                services.cover.delete()  # Удаляем файл из хранилища
                services.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if services.previev:
                services.previev.delete()
                services.previev = None

        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            ServiceMedia.objects.filter(
                id__in=delete_files_ids.split(","), service=services
            ).delete()

        # Сохраняем изменения
        services.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        files = self.request.FILES.getlist("files")
        for file in files:
            ServiceMedia.objects.create(service=services, file=file)

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ServicesUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = "moderations/service_form.html"
    success_url = reverse_lazy("moderation:service_settings")
    context_object_name = "services"

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        services = form.save(commit=False)

        # Обработка удаления обложки (cover)
        if self.request.POST.get("delete_cover") == "true":
            if services.cover:
                services.cover.delete()  # Удаляем файл из хранилища
                services.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if services.previev:
                services.previev.delete()
                services.previev = None

        # Сохраняем изменения
        services.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Это поможет вам увидеть ошибки валидации
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.object:
            context["existing_files"] = self.object.servicemedia_set.all()

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PricesSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/price_settings.html"
    model = Price
    context_object_name = "price_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        price = Price.objects.all().order_by("-create")

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            price = price.filter(name__icontains=search_name)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                price = price.filter(create__date=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(price, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            price_list = paginator.page(page)
        except PageNotAnInteger:
            price_list = paginator.page(1)
        except EmptyPage:
            price_list = paginator.page(paginator.num_pages)

        context["price_list"] = price_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = price_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PricesCreateView(LoginRequiredMixin, CreateView):
    model = Price
    form_class = PriceForm
    template_name = "moderations/price_form.html"
    success_url = reverse_lazy("moderation:price_settings")
    context_object_name = "prices"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = CategorysBlogs.objects.all()
        return context

    def form_valid(self, form):
        prices = form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Это поможет вам увидеть ошибки валидации
        return super().form_invalid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PricesUpdateView(LoginRequiredMixin, UpdateView):
    model = Price
    form_class = PriceForm
    template_name = "moderations/price_form.html"
    success_url = reverse_lazy("moderation:price_settings")
    context_object_name = "prices"

    def form_valid(self, form):
        prices = form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Это поможет вам увидеть ошибки валидации
        return super().form_invalid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class BlogCreateView(LoginRequiredMixin, CreateView):
    model = Blogs
    form_class = BlogsForm
    template_name = "moderations/blogs_form.html"
    success_url = reverse_lazy("moderation:blog_settings")
    context_object_name = "blogs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = CategorysBlogs.objects.all()
        return context

    def form_valid(self, form):
        blogs = form.save()
        category = self.request.POST.getlist("category")

        if category:
            blogs.category.clear()
            for category_id in category:
                category = get_object_or_404(CategorysBlogs, id=category_id)
                blogs.category.add(category)

        if self.request.POST.get("delete_cover") == "true":
            if blogs.cover:
                blogs.cover.delete()  # Удаляем файл из хранилища
                blogs.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if blogs.previev:
                blogs.previev.delete()
                blogs.previev = None

        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Это поможет вам увидеть ошибки валидации
        return super().form_invalid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class BlogUpdateView(LoginRequiredMixin, UpdateView):
    model = Blogs
    form_class = BlogsForm
    template_name = "moderations/blogs_form.html"
    success_url = reverse_lazy("moderation:blog_settings")
    context_object_name = "blogs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = CategorysBlogs.objects.all()
        context["categories"] = categories

        return context

    def form_valid(self, form):
        blogs = form.save()
        category = self.request.POST.getlist("category")

        if category:
            blogs.category.clear()
            for category_id in category:
                category = get_object_or_404(CategorysBlogs, id=category_id)
                blogs.category.add(category)

        if self.request.POST.get("delete_cover") == "true":
            if blogs.cover:
                blogs.cover.delete()  # Удаляем файл из хранилища
                blogs.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if blogs.previev:
                blogs.previev.delete()
                blogs.previev = None

        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Это поможет вам увидеть ошибки валидации
        return super().form_invalid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class BlogDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:blog_settings")

    def post(self, request):
        data = json.loads(request.body)
        blogs_ids = data.get("blogs_ids", [])
        if blogs_ids:
            Blogs.objects.filter(id__in=blogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class GalleryDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:gallery_settings")

    def post(self, request):
        data = json.loads(request.body)
        gallery_ids = data.get("gallery_ids", [])
        if gallery_ids:
            Gallery.objects.filter(id__in=gallery_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ServicesDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:service_settings")

    def post(self, request):
        data = json.loads(request.body)
        service_ids = data.get("service_ids", [])
        if service_ids:
            Service.objects.filter(id__in=service_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PricesDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:price_settings")

    def post(self, request):
        data = json.loads(request.body)
        price_ids = data.get("price_ids", [])
        if price_ids:
            Price.objects.filter(id__in=price_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# Благотворительность
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SponsorshipSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/sponsorship_settings.html"
    model = Sponsorship
    context_object_name = "sponsorship_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sponsorships = Sponsorship.objects.all()

        # Фильтрация по имени
        search_name = self.request.GET.get("search_name", "")
        if search_name:
            sponsorships = sponsorships.filter(name__icontains=search_name)

        # Фильтрация по дате
        search_date = self.request.GET.get("search_date", "")
        if search_date:
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                sponsorships = sponsorships.filter(create__date=search_date)
            except ValueError:
                pass  # Игнорируем ошибки в формате даты

        # Фильтрация по категории (если такая связь есть)
        search_category = self.request.GET.get("search_category", "")
        if search_category:
            sponsorships = sponsorships.filter(category__id=search_category)

        # Пагинация
        paginator = Paginator(sponsorships, 10)  # 10 элементов на страницу
        page = self.request.GET.get("page")

        try:
            sponsorships_list = paginator.page(page)
        except PageNotAnInteger:
            sponsorships_list = paginator.page(1)
        except EmptyPage:
            sponsorships_list = paginator.page(paginator.num_pages)

        context["sponsorships_list"] = (
            sponsorships_list  # Передаем отфильтрованные элементы
        )
        context["paginator"] = paginator
        context["page_obj"] = sponsorships_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SponsorshipsCreateView(LoginRequiredMixin, CreateView):
    model = Sponsorship
    form_class = SponsorshipForm
    template_name = "moderations/sponsorship_form.html"
    success_url = reverse_lazy("moderation:sponsorship_settings")
    context_object_name = "blogs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blogs"] = Blogs.objects.all()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SponsorshipUpdateView(LoginRequiredMixin, UpdateView):
    model = Sponsorship
    form_class = SponsorshipForm
    template_name = "moderations/sponsorship_form.html"
    success_url = reverse_lazy("moderation:sponsorship_settings")
    context_object_name = "sponsorships"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SponsorshipDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:sponsorship_settings")

    def post(self, request):
        data = json.loads(request.body)
        sponsorships_ids = data.get("sponsorships_ids", [])
        if sponsorships_ids:
            Sponsorship.objects.filter(id__in=sponsorships_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PagesSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/pages_settings.html"
    model = Pages
    context_object_name = "pages_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pages = Pages.objects.all()
        context["pagetypes"] = Pages.PAGETYPE

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            pages = pages.filter(name__icontains=search_name)

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            pages = pages.filter(slug__icontains=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            pages = pages.filter(pagetype=search_type)

        # Пагинация
        paginator = Paginator(pages, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            pages_list = paginator.page(page)
        except PageNotAnInteger:
            pages_list = paginator.page(1)
        except EmptyPage:
            pages_list = paginator.page(paginator.num_pages)

        context["pages_list"] = pages_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = pages_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PagesCreateView(LoginRequiredMixin, CreateView):
    model = Pages
    form_class = PagesForm
    template_name = "moderations/pages_form.html"
    success_url = reverse_lazy("moderation:pages_settings")
    context_object_name = "pages"

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        pages = form.save(commit=False)
        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if pages.previev:
                pages.previev.delete()
                pages.previev = None

        # Сохраняем изменения
        pages.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Проверьте, есть ли ошибки валидации
        return super().form_invalid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PagesUpdateView(LoginRequiredMixin, UpdateView):
    model = Pages
    form_class = PagesForm
    template_name = "moderations/pages_form.html"
    success_url = reverse_lazy("moderation:pages_settings")
    context_object_name = "pages"

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        pages = form.save(commit=False)
        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_previev") == "true":
            if pages.previev:
                pages.previev.delete()
                pages.previev = None

        # Сохраняем изменения
        pages.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PagesDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:pages_settings")

    def post(self, request):
        data = json.loads(request.body)
        pages_ids = data.get("pages_ids", [])
        if pages_ids:
            Pages.objects.filter(id__in=pages_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SeoSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/seosettings.html"
    model = Seo
    context_object_name = "seo_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seo = Seo.objects.all()
        context["pagetypes"] = Seo.PAGE_CHOICE

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            seo = seo.filter(title__icontains=search_name)

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            seo = seo.filter(pk=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            seo = seo.filter(pagetype=search_type)

        # Пагинация
        paginator = Paginator(seo, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            seo_list = paginator.page(page)
        except PageNotAnInteger:
            seo_list = paginator.page(1)
        except EmptyPage:
            seo_list = paginator.page(paginator.num_pages)

        context["seo_list"] = seo_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = seo_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SeoCreateView(LoginRequiredMixin, CreateView):
    model = Seo
    form_class = SeoForm
    template_name = "moderations/seoform.html"
    success_url = reverse_lazy("moderation:seo_settings")
    context_object_name = "seo"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SeoUpdateView(LoginRequiredMixin, UpdateView):
    model = Seo
    form_class = SeoForm
    template_name = "moderations/seoform.html"
    success_url = reverse_lazy("moderation:seo_settings")
    context_object_name = "seo"

    def form_valid(self, form):
        form.instance.setting = SettingsGlobale.objects.first()
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SeoDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:seo_settings")

    def post(self, request, seo_id):
        seo = get_object_or_404(Seo, pk=seo_id)
        seo.delete()
        return redirect("moderation:seo_settings")


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SeoDeleteMultipleView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:seo_settings")

    def post(self, request):
        data = json.loads(request.body)
        seo_ids = data.get("seo_ids", [])
        if seo_ids:
            Seo.objects.filter(id__in=seo_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class NotificationSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/notifications_settings.html"
    model = Notificationgroups
    context_object_name = "notification_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notifications = Notificationgroups.objects.all()
        context["content_types"] = ContentType.objects.all()
        context["users"] = get_user_model().objects.all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            notifications = notifications.filter(object_id=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            notifications = notifications.filter(content_type=search_type)

        user_id = self.request.GET.get("user_id", "")
        if user_id:
            notifications = notifications.filter(user__id=user_id)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                notifications = notifications.filter(created_at__date=search_date)
            except ValueError:
                pass

        paginator = Paginator(notifications, 10)
        page = self.request.GET.get("page")
        try:
            notifications_list = paginator.page(page)
        except PageNotAnInteger:
            notifications_list = paginator.page(1)
        except EmptyPage:
            notifications_list = paginator.page(paginator.num_pages)

        context["notifications_list"] = notifications_list
        context["paginator"] = paginator
        context["page_obj"] = notifications_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class NotificationCreateView(LoginRequiredMixin, CreateView):
    model = Notificationgroups
    form_class = NotificationForm
    template_name = "moderations/notifications_form.html"
    success_url = reverse_lazy("moderation:notifications_settings")
    context_object_name = "notifications"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class NotificationDeleteMultipleView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:seo_settings")

    def post(self, request):
        data = json.loads(request.body)
        notification_ids = data.get("notification_ids", [])
        if notification_ids:
            Notificationgroups.objects.filter(id__in=notification_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class NotificationView(ListView):
    model = Notification
    template_name = "lk/notification_list.html"
    context_object_name = "notificationes"
    paginate_by = 30

    def get_queryset(self):
        # Добавляем отладочный вывод
        queryset = Notification.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        print(
            f"Notifications for user {self.request.user}: {queryset}"
        )  # Выводим queryset для отладки
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


@login_required()
def save_categories(request, slug):
    # Получаем объект блога по slug
    blog = get_object_or_404(Blogs, slug=slug)

    if request.method == "GET":
        categories = request.GET.get("categories", "")
        if categories:
            category_list = categories.split(",")
            blog.category.clear()
            for category_id in category_list:
                category = get_object_or_404(CategorysBlogs, id=category_id)
                blog.category.add(category)

            return JsonResponse(
                {"status": "success", "message": "Categories saved successfully."}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "No categories provided."}, status=400
            )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid request method."}, status=400
        )


@login_required()
def create_category(request):
    if request.method == "POST":
        name = request.POST.get("name")
        slug = request.POST.get("slug")
        description = request.POST.get("description")
        title = request.POST.get("title")
        content = request.POST.get("content")
        parent_id = request.POST.get("parent")
        cover = request.FILES.get("cover")
        icon = request.FILES.get("icon")
        image = request.FILES.get("image")
        site_id = request.POST.get("site")

        category = CategorysBlogs.objects.create(
            name=name,
            slug=slug,
            description=description,
            title=title,
            content=content,
            parent_id=parent_id,
            cover=cover,
            icon=icon,
            image=image,
            site_id=1,
        )

        return JsonResponse({"success": True, "category_id": category.id})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def category_list(request):
    categories = CategorysBlogs.objects.all().values(
        "id", "name"
    )  # Получаем нужные поля
    return JsonResponse({"categories": list(categories)})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategorysBlogsSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/categorys_settings.html"
    model = CategorysBlogs
    context_object_name = "categorys_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categorys = CategorysBlogs.objects.all()

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            categorys = categorys.filter(name__icontains=search_name)

        search_category = self.request.GET.get("search_category", "")
        if search_category:
            categorys = categorys.filter(parent__id=search_category)

        # Пагинация
        paginator = Paginator(categorys, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            categorys_list = paginator.page(page)
        except PageNotAnInteger:
            categorys_list = paginator.page(1)
        except EmptyPage:
            categorys_list = paginator.page(paginator.num_pages)

        context["categorys_list"] = categorys_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = categorys_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategorysBlogsCreateView(LoginRequiredMixin, CreateView):
    model = CategorysBlogs
    form_class = CategorysBlogsForm
    template_name = "moderations/categorys_form.html"
    success_url = reverse_lazy("moderation:categorys_settings")
    context_object_name = "Categorys"

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        category = form.save(commit=False)

        # Обработка удаления обложки (cover)
        if self.request.POST.get("delete_cover") == "true":
            if category.cover:
                category.cover.delete()  # Удаляем файл из хранилища
                category.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_icon") == "true":
            if category.previev:
                category.previev.delete()
                category.previev = None

        if self.request.POST.get("delete_image") == "true":
            if category.image:
                category.image.delete()
                category.image = None
        # Сохраняем изменения
        category.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategorysBlogsUpdateView(LoginRequiredMixin, UpdateView):
    model = CategorysBlogs
    form_class = CategorysBlogsForm
    template_name = "moderations/categorys_form.html"
    success_url = reverse_lazy("moderation:categorys_settings")
    context_object_name = "categorys"

    def form_valid(self, form):
        # Получаем экземпляр объекта до сохранения
        category = form.save(commit=False)

        # Обработка удаления обложки (cover)
        if self.request.POST.get("delete_cover") == "true":
            if category.cover:
                category.cover.delete()  # Удаляем файл из хранилища
                category.cover = None  # Сбрасываем поле в модели

        # Обработка удаления превью (previev)
        if self.request.POST.get("delete_icon") == "true":
            if category.icon:
                category.icon.delete()
                category.icon = None

        if self.request.POST.get("delete_image") == "true":
            if category.image:
                category.image.delete()
                category.image = None
        # Сохраняем изменения
        category.save()
        form.save_m2m()  # Необходимо для сохранения ManyToMany полей

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategorysBlogsDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:categorys_settings")

    def post(self, request):
        data = json.loads(request.body)
        categorysblogs_ids = data.get("categorysblogs_ids", [])
        if categorysblogs_ids:
            CategorysBlogs.objects.filter(id__in=categorysblogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# Tags


@login_required()
def save_tags(request, slug):
    # Получаем объект блога по slug
    blog = get_object_or_404(Blogs, slug=slug)

    if request.method == "GET":
        tags = request.GET.get("tags", "")
        if tags:
            tag_list = tags.split(",")
            blog.tag.clear()
            for tag_id in tag_list:
                tag = get_object_or_404(TagsBlogs, id=tag_id)
                blog.tag.add(tag)

            return JsonResponse(
                {"status": "success", "message": "Categories saved successfully."}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "No categories provided."}, status=400
            )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid request method."}, status=400
        )


@login_required()
def create_tag(request):
    if request.method == "POST":
        name = request.POST.get("name")
        slug = request.POST.get("slug")
        description = request.POST.get("description")
        title = request.POST.get("title")
        content = request.POST.get("content")
        parent_id = request.POST.get("parent")
        cover = request.FILES.get("cover")
        icon = request.FILES.get("icon")
        image = request.FILES.get("image")
        site_id = request.POST.get("site")

        tag = TagsBlogs.objects.create(
            name=name,
            slug=slug,
            description=description,
            title=title,
            content=content,
            parent_id=parent_id,
            cover=cover,
            icon=icon,
            image=image,
            site_id=1,
        )

        return JsonResponse({"success": True, "tag_id": tag.id})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def tag_list(request):
    tags = TagsBlogs.objects.all().values("id", "name")  # Получаем нужные поля
    return JsonResponse({"tags": list(tags)})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TagsBlogsSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/tags_settings.html"
    model = TagsBlogs
    context_object_name = "tags_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = TagsBlogs.objects.all()

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            tags = tags.filter(name__icontains=search_name)

        search_tag = self.request.GET.get("search_tag", "")
        if search_tag:
            tags = tags.filter(parent__id=search_tag)

        # Пагинация
        paginator = Paginator(tags, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            tags_list = paginator.page(page)
        except PageNotAnInteger:
            tags_list = paginator.page(1)
        except EmptyPage:
            tags_list = paginator.page(paginator.num_pages)

        context["tags_list"] = tags_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = tags_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TagsBlogsCreateView(LoginRequiredMixin, CreateView):
    model = TagsBlogs
    form_class = TagsBlogsForm
    template_name = "moderations/tags_form.html"
    success_url = reverse_lazy("moderation:tags_settings")
    context_object_name = "tags"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TagsBlogsUpdateView(LoginRequiredMixin, UpdateView):
    model = TagsBlogs
    form_class = TagsBlogsForm
    template_name = "moderations/tags_form.html"
    success_url = reverse_lazy("moderation:tags_settings")
    context_object_name = "tags"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TagsBlogsDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:tags_settings")

    def post(self, request):
        data = json.loads(request.body)
        tagsblogs_ids = data.get("tagsblogs_ids", [])
        if tagsblogs_ids:
            TagsBlogs.objects.filter(id__in=tagsblogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PaymentSettings(LoginRequiredMixin, ListView):
    template_name = "moderations/payment_settings.html"
    model = PaymentType
    context_object_name = "payment_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment = PaymentType.objects.all()
        context["types"] = PaymentType.TYPE

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            payment = payment.filter(shop_key__icontains=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            payment = payment.filter(type=search_type)

        # Пагинация
        paginator = Paginator(payment, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            payment_list = paginator.page(page)
        except PageNotAnInteger:
            payment_list = paginator.page(1)
        except EmptyPage:
            payment_list = paginator.page(paginator.num_pages)

        context["payment_list"] = payment_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = payment_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = "moderations/payment_form.html"
    success_url = reverse_lazy("moderation:payment_settings")
    context_object_name = "payment"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PaymentUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentType
    form_class = PaymentTypeForm
    template_name = "moderations/payment_form.html"
    success_url = reverse_lazy("moderation:payment_settings")
    context_object_name = "payment"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PaymentDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:payment_settings")

    def post(self, request):
        data = json.loads(request.body)
        payment_ids = data.get("payment_ids", [])
        if payment_ids:
            PaymentType.objects.filter(id__in=payment_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SchoolPage(LoginRequiredMixin, TemplateView):
    template_name = "moderations/school.html"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = "moderations/template/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        now = timezone.now()
        first_day_of_month = now.replace(day=1)
        last_month = now - timezone.timedelta(days=30)
        today = now.date()

        User = get_user_model()
        new_users_count = User.objects.filter(
            type=1, date_joined__gte=last_month
        ).count()

        today_withdrawals_sum = (
                Withdrawal.objects.filter(create__date=today, type=0).aggregate(
                    total=Sum("amount")
                )["total"]
                or 0
        )

        monthly_withdrawals_sum = (
                Withdrawal.objects.filter(
                    create__date__gte=first_day_of_month, type=0
                ).aggregate(total=Sum("amount"))["total"]
                or 0
        )

        context["tickets"] = Ticket.objects.filter(status=0).order_by("-date")
        context["ticket_count"] = Ticket.objects.count()
        context["user_count"] = user_count
        context["new_users_count"] = new_users_count
        context["today_withdrawals_sum"] = today_withdrawals_sum
        context["monthly_withdrawals_sum"] = monthly_withdrawals_sum

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class Documentation(LoginRequiredMixin, TemplateView):
    template_name = "moderations/documentation.html"
    model = Documentations
    context_object_name = "docs_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        docs = Documentations.objects.all()

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            docs = docs.filter(name__icontains=search_name)

        paginator = Paginator(docs, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            docs_list = paginator.page(page)
        except PageNotAnInteger:
            docs_list = paginator.page(1)
        except EmptyPage:
            docs_list = paginator.page(paginator.num_pages)

        context["docs_list"] = docs_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = docs_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class DocumentationCreateView(LoginRequiredMixin, CreateView):
    model = Documentations
    form_class = DocumentationForm
    template_name = "moderations/documentation_create.html"
    context_object_name = "documentation"

    @transaction.atomic
    def form_valid(self, form):
        # Сохраняем документ
        comment = form.save(commit=False)
        comment.save()

        # Сохраняем загруженные файлы
        files = self.request.FILES.getlist("files")
        for file in files:
            DocumentationsMedia.objects.create(documentations=comment, file=file)

        # Редирект на страницу обновления документации
        return redirect(reverse("moderation:docs_update", args=[comment.id]))

    def form_invalid(self, form):
        print(form.errors)  # Для отладки
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class UploadFileView(View):
    def post(self, request, documentation_id):
        file = request.FILES.get("file")
        documentation = get_object_or_404(Documentations, id=documentation_id)
        documentation_file = DocumentationsMedia.objects.create(
            file=file, documentations=documentation
        )

        return JsonResponse(
            {
                "success": True,
                "file": {
                    "id": documentation_file.id,
                    "url": documentation_file.file.url,
                    "name": documentation_file.file.name,
                },
            }
        )


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class DeleteFileView(View):
    def delete(self, request, file_id):
        file = get_object_or_404(DocumentationsMedia, id=file_id)
        file.delete()
        return JsonResponse({"success": True})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class DocumentationUpdateView(LoginRequiredMixin, UpdateView):
    model = Documentations
    form_class = DocumentationForm
    template_name = "moderations/documentation_detail.html"
    success_url = reverse_lazy("moderation:documentation")
    context_object_name = "documentation"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documentation = self.get_object()
        documentation_files = documentation.documentations.all()

        # Пагинация
        paginator = Paginator(documentation_files, 4)  # 10 элементов на страницу
        page = self.request.GET.get("page")
        try:
            files_list = paginator.page(page)
        except PageNotAnInteger:
            files_list = paginator.page(1)
        except EmptyPage:
            files_list = paginator.page(paginator.num_pages)

        context["documentation_files"] = files_list  # Передаем отфильтрованные файлы
        context["paginator"] = paginator
        context["page_obj"] = files_list
        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class DocumentationDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:documentation")

    def post(self, request):
        data = json.loads(request.body)
        docs_ids = data.get("docs_ids", [])
        if docs_ids:
            Documentations.objects.filter(id__in=docs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductExpensePositionList(LoginRequiredMixin, ListView):
    template_name = "moderations/product_expense_position_list.html"
    model = ProductExpensePosition
    context_object_name = "product_expense_positions"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faq = Storage.objects.all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            faq = faq.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            faq = faq.filter(question__icontains=search_name)

        # Пагинация
        paginator = Paginator(faq, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductExpensePositionCreateView(CreateView):
    model = ProductExpensePosition
    form_class = ProductExpensePositionForm
    template_name = 'moderations/products_expense_position_form.html'
    success_url = reverse_lazy("moderation:product_expense_position")
    context_object_name = "pages"

    @transaction.atomic
    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.save()

        return redirect('moderation:product_expense_position')

    def form_invalid(self, form):
        print(form.errors)  # Для отладки
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductExpensePositionUpdateView(UpdateView):
    model = ProductExpensePosition
    form_class = ProductExpensePositionForm
    template_name = "moderations/products_expense_position_form.html"
    success_url = reverse_lazy("moderation:product_expense_position")
    context_object_name = "expenses"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = CategorysBlogs.objects.all()
        context["categories"] = categories

        return context

    def form_valid(self, form):
        expenses = form.save()

        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Это поможет вам увидеть ошибки валидации
        return super().form_invalid(form)


@require_POST
@csrf_exempt
def expenses_delete(request):
    try:
        # Парсим JSON данные из запроса
        data = json.loads(request.body)
        expense_ids = data.get('expense_ids', [])

        if not expense_ids:
            return JsonResponse({'success': False, 'error': 'No expenses selected'}, status=400)

        deleted_count, _ = ProductExpensePosition.objects.filter(id__in=expense_ids).delete()

        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} expenses'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductExpensePurchaseList(LoginRequiredMixin, ListView):
    template_name = "moderations/product_expense_purchase_list.html"
    model = ProductExpensePurchase
    context_object_name = "product_expense_purchase"
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faq = Storage.objects.all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            faq = faq.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            faq = faq.filter(question__icontains=search_name)

        # Пагинация
        paginator = Paginator(faq, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductExpensePurchaseCreateView(CreateView):
    model = ProductExpensePurchase
    form_class = ProductExpensePurchaseForm
    template_name = 'moderations/product_expense_purchase_form.html'
    success_url = reverse_lazy("moderation:product_expense_position")
    context_object_name = "pages"

    @transaction.atomic
    def form_valid(self, form):
        form.save()
        return redirect('moderation:product_purchase_list')

    def form_invalid(self, form):
        print(form.errors)  # Для отладки
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductExpensePurchaseUpdateView(UpdateView):
    model = ProductExpensePurchase
    form_class = ProductExpensePurchaseForm
    template_name = "moderations/product_expense_purchase_form.html"
    success_url = reverse_lazy("moderation:product_purchase_list")
    context_object_name = "expenses"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = CategorysBlogs.objects.all()
        context["categories"] = categories

        return context

    def form_valid(self, form):
        expenses = form.save()

        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Это поможет вам увидеть ошибки валидации
        return super().form_invalid(form)


@require_POST
@csrf_exempt
def purchase_expenses_delete(request):
    try:
        # Парсим JSON данные из запроса
        data = json.loads(request.body)
        expense_ids = data.get('expense_ids', [])

        if not expense_ids:
            return JsonResponse({'success': False, 'error': 'No expenses selected'}, status=400)

        deleted_count, _ = ProductExpensePurchase.objects.filter(id__in=expense_ids).delete()

        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} expenses'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


"""Тикеты"""


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TicketsView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = "moderations/tickets.html"
    context_object_name = "tickets"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = Ticket.objects.order_by("-date").all()
        context["statuses"] = Ticket.STATUS_CHOICES
        user = self.request.user

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            ticket = ticket.filter(themas__icontains=search_name)

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            ticket = ticket.filter(id__icontains=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            ticket = ticket.filter(status=search_type)

        for_me = self.request.GET.get("for_me", "")
        if for_me:
            ticket = ticket.filter(manager=user)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                ticket = ticket.filter(date__date=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(ticket, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            ticket_list = paginator.page(page)
        except PageNotAnInteger:
            ticket_list = paginator.page(1)
        except EmptyPage:
            ticket_list = paginator.page(paginator.num_pages)

        context["ticket_list"] = ticket_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = ticket_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TicketMessageView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = "moderations/tickets_messages.html"
    context_object_name = "ticket"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket = self.object

        # Get all comments related to the ticket
        comments = (
            TicketComment.objects.filter(ticket=ticket).prefetch_related("media").all()
        )

        # Setup pagination
        paginator = Paginator(comments, 10)  # Show 10 comments per page
        page = self.request.GET.get("page")

        try:
            comments_paginated = paginator.page(page)
        except PageNotAnInteger:
            comments_paginated = paginator.page(1)
        except EmptyPage:
            comments_paginated = paginator.page(paginator.num_pages)

        context["ticket_comments"] = comments_paginated
        context["form"] = TicketCommentForm()
        context["ticket"] = ticket
        context["paginator"] = paginator
        context["page_obj"] = comments_paginated

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TicketDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:tickets")

    def post(self, request):
        data = json.loads(request.body)
        ticket_ids = data.get("ticket_ids", [])
        if ticket_ids:
            Ticket.objects.filter(id__in=ticket_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class TicketCommentCreateView(LoginRequiredMixin, CreateView):
    model = TicketComment
    form_class = TicketCommentForm

    @transaction.atomic
    def form_valid(self, form):
        ticket_id = self.kwargs["ticket_id"]
        ticket = get_object_or_404(Ticket, id=ticket_id)
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = self.request.user
        comment.save()

        files = self.request.FILES.getlist("files")
        for file in files:
            TicketCommentMedia.objects.create(comment=comment, file=file)

        return JsonResponse(
            {
                "status": "success",
                "comment": {
                    "id": comment.id,
                    "author": comment.author.username,
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


"""Заявки"""


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CollaborationsList(LoginRequiredMixin, ListView):
    template_name = "moderations/collaborations.html"
    model = Collaborations
    context_object_name = "collaboration"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collaborations = Collaborations.objects.all()

        # Фильтрация
        name_value = self.request.GET.get("name")
        email_value = self.request.GET.get("email")
        subject_value = self.request.GET.get("subject")
        phone_value = self.request.GET.get("phone")
        message_value = self.request.GET.get("message")

        if name_value:
            collaborations = collaborations.filter(name__icontains=name_value)

        if email_value:
            collaborations = collaborations.filter(email__icontains=email_value)

        if subject_value:
            collaborations = collaborations.filter(subject__icontains=subject_value)

        if phone_value:
            collaborations = collaborations.filter(phone__icontains=phone_value)

        # Пагинация
        paginator = Paginator(collaborations, self.paginate_by)
        page = self.request.GET.get("page")
        try:
            collaborations_list = paginator.page(page)
        except PageNotAnInteger:
            collaborations_list = paginator.page(1)
        except EmptyPage:
            collaborations_list = paginator.page(paginator.num_pages)

        # Добавляем данные в контекст
        context["collaborations_list"] = collaborations_list
        context["paginator"] = paginator
        context["page_obj"] = collaborations_list

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CollaborationsUpdateView(LoginRequiredMixin, UpdateView):
    model = Collaborations
    form_class = CollaborationsForm
    template_name = "moderations/сollaborations_form.html"
    success_url = reverse_lazy("moderation:collaborations_list")
    context_object_name = "collaboration"  # Исправлено на единственное число
    pk_url_kwarg = "pk"

    def form_valid(self, form):
        # Дополнительная обработка перед сохранением
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CollaborationsDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:collaborations_list")

    def post(self, request):
        try:
            data = json.loads(request.body)
            collaborations_ids = data.get("collaborations_ids", [])

            if collaborations_ids:
                Collaborations.objects.filter(id__in=collaborations_ids).delete()
                return JsonResponse(
                    {
                        "status": "success",
                        "redirect": reverse("moderation:collaborations_list"),
                    }
                )

            return JsonResponse(
                {"status": "error", "message": "Нет ID для удаления"}, status=400
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Неверный формат запроса"}, status=400
            )


"""Пользователь"""


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SignUpClientView(LoginRequiredMixin, CreateView):
    form_class = SignUpForm
    template_name = "moderations/register.html"
    success_url = reverse_lazy("moderation:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class WorkerListView(ListView):
    model = Profile
    template_name = "moderations/worker_list.html"
    context_object_name = "users"
    paginate_by = 13

    def get_queryset(self):
        query = self.request.GET.get("q")
        queryset = (
            Profile.objects.filter(type=0)
            .exclude(id=self.request.user.id)
            .order_by("id")
        )

        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(middle_name__icontains=query)
            )

        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "moderations/worker_list_partial.html", context, request=self.request
            )
            return JsonResponse({"html": html})
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = Profile.objects.filter(
            type=0
        ).count()  # Общее количество пользователей type=0
        return context


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class ClientListView(ListView):
    model = Profile
    template_name = "moderations/client_list.html"
    context_object_name = "users"
    paginate_by = 13

    def get_queryset(self):
        query = self.request.GET.get("q")
        queryset = (
            Profile.objects.filter(Q(type=2) | Q(type=3))
            .exclude(id=self.request.user.id)
            .order_by("id")
        )

        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(middle_name__icontains=query)
            )

        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "moderations/client_list_partial.html", context, request=self.request
            )
            return JsonResponse({"html": html})
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = Profile.objects.filter(
            type=2
        ).count()  # Общее количество пользователей
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SignUpWorkerView(LoginRequiredMixin, CreateView):
    form_class = SignUpForm
    template_name = "moderations/worker_register.html"
    success_url = reverse_lazy("moderation:worker_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.type = 0
        user.save()
        messages.success(self.request, "Пользователь успешно зарегистрирован!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Ошибка при регистрации. Проверьте данные.")
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SignUpView(LoginRequiredMixin, CreateView):
    form_class = SignUpForm
    template_name = "moderations/worker_register.html"
    success_url = reverse_lazy("moderation:user_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.type = 1
        user.save()
        messages.success(self.request, "Пользователь успешно зарегистрирован!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Ошибка при регистрации. Проверьте данные.")
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SignClientUpView(LoginRequiredMixin, CreateView):
    form_class = SignUpClientForm
    template_name = "moderations/client_register.html"
    success_url = reverse_lazy("moderation:clients_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.type = 3 if form.cleaned_data["is_company"] else 2  # Устанавливаем тип
        user.save()
        messages.success(self.request, "Пользователь успешно зарегистрирован!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Ошибка при регистрации. Проверьте данные.")
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PartnerListView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = "moderations/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        queryset = Profile.objects.filter(type=3)  # Фильтрация по типу

        # Фильтрация по имени
        search_name = self.request.GET.get("search_name", "")
        if search_name:
            queryset = queryset.filter(username__icontains=search_name)

        # Фильтрация по ID
        search_phone = self.request.GET.get("search_phone", "")
        if search_phone:
            queryset = queryset.filter(phone__icontains=search_phone)

        user_id = self.request.GET.get("user_id", "")
        if user_id:
            queryset = queryset.filter(id=user_id)

        # Фильтрация по дате рождения
        search_date = self.request.GET.get("search_date", "")
        if search_date:
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                queryset = queryset.filter(birthday=search_date)
            except ValueError:
                pass  # Если формат даты неверный, просто игнорируем

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Пагинация
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        page = self.request.GET.get("page")
        try:
            user_list = paginator.page(page)
        except PageNotAnInteger:
            user_list = paginator.page(1)
        except EmptyPage:
            user_list = paginator.page(paginator.num_pages)

        context["user_list"] = user_list  # Передаем отфильтрованные пользователи
        context["paginator"] = paginator
        context["page_obj"] = user_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SignUpPartnerView(LoginRequiredMixin, CreateView):
    form_class = SignUpForm
    template_name = "moderations/register.html"
    success_url = reverse_lazy("moderation:partner")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        print(self.request.user.id)
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password1"])
        user.type = 3
        user.save()  # Сначала сохраняем пользователя

        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = Profile
    template_name = "moderations/user_confirm_delete.html"
    success_url = reverse_lazy(
        "moderation:user_list"
    )  # URL для перенаправления после удаления

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return redirect(success_url)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class UsersDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:user_list")

    def post(self, request):
        data = json.loads(request.body)
        user_ids = data.get("user_ids", [])
        if user_ids:
            Profile.objects.filter(id__in=user_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class WorkerDeleteView(DeleteView):
    model = Profile
    template_name = "moderations/user_confirm_delete.html"
    success_url = reverse_lazy(
        "moderation:worker_list"
    )  # URL для перенаправления после удаления

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # Добавьте здесь проверку прав доступа, например, что пользователь имеет право удалять профили
        # Пример: только суперпользователь или администраторы могут удалять профили
        if not self.request.user.is_superuser:
            raise PermissionDenied("У вас нет прав для удаления профиля.")
        return obj

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return redirect(success_url)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class BlockUserView(View):
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        user = get_object_or_404(Profile, pk=user_id)
        user.blocked = True
        user.save()

        # Получаем предыдущий URL из заголовка HTTP_REFERER
        previous_url = request.META.get("HTTP_REFERER", "moderation:user_list")
        return HttpResponseRedirect(previous_url)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class UnblockUserView(View):
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        user = get_object_or_404(Profile, pk=user_id)
        user.blocked = False
        user.save()

        # Получаем предыдущий URL из заголовка HTTP_REFERER
        previous_url = request.META.get("HTTP_REFERER", "moderation:user_list")
        return HttpResponseRedirect(previous_url)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class RestoreUserView(View):
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        user = get_object_or_404(Profile, pk=user_id)
        user.deleted = False
        user.save()

        # Получаем предыдущий URL из заголовка HTTP_REFERER
        previous_url = request.META.get("HTTP_REFERER", "moderation:user_list")
        return HttpResponseRedirect(previous_url)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class DeleteUserView(View):
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get("pk")
        user = get_object_or_404(Profile, pk=user_id)
        user.deleted = True
        user.save()

        # Получаем предыдущий URL из заголовка HTTP_REFERER
        previous_url = request.META.get("HTTP_REFERER", "moderation:user_list")
        return HttpResponseRedirect(previous_url)


@method_decorator(login_required(login_url="moderation:dashboard"), name="dispatch")
class EditWorkerProfileView(UpdateView):
    model = Profile
    form_class = WorkerUpdateProfileForm
    template_name = "moderations/worker_edit.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, id=self.kwargs.get("user_id"))

    def get_success_url(self):
        return reverse_lazy("moderation:worker_list")

    def form_invalid(self, form):
        print("Форма невалидна", form.errors)  # Логируем ошибки в консоль
        return self.render_to_response(self.get_context_data(form=form))

    def get_initial(self):
        initial = super().get_initial()
        if self.object.birthday:
            initial["birthday"] = self.object.birthday.strftime("%Y-%m-%d")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = self.object
        context["form_errors"] = (
            kwargs.get("form").errors if "form" in kwargs else None
        )  # Добавляем ошибки в контекст

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EditProfileView(LoginRequiredMixin, TemplateView):
    template_name = "moderations/profile_edit_user.html"

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        profile_id = kwargs.get("pk")  # Получаем ID профиля из URL
        profile = get_object_or_404(Profile, id=profile_id)

        # Искусственно вызываем ошибку
        if profile_id == 1:
            raise Exception("Ошибка: запрещено редактировать профиль с ID 1.")

        # Проверяем доступ текущего пользователя к редактированию профиля
        if request.user.is_superuser or request.user == profile.user:
            initial_data = {
                "birthday": profile.birthday.strftime("%Y-%m-%d")
                if profile.birthday
                else None
            }
            form = UserProfileForm(instance=profile, initial=initial_data)
            context = self.get_context_data(
                form=form, title="Личные данные", profile=profile
            )
            return self.render_to_response(context)
        else:
            return HttpResponseForbidden(
                "У вас нет прав для редактирования этого профиля."
            )

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        profile_id = kwargs.get("pk")  # Получаем ID профиля из URL
        profile = get_object_or_404(Profile, id=profile_id)

        # Искусственно вызываем ошибку
        if "force_error" in request.POST:
            return HttpResponseBadRequest("Произошла ошибка при обработке данных.")

        if not (request.user.is_superuser or request.user == profile.user):
            return HttpResponseForbidden(
                "У вас нет прав для редактирования этого профиля."
            )

        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("moderation:edit_profiles", pk=profile_id)
        else:
            context = self.get_context_data(
                form=form, title="Личные данные", profile=profile
            )
        return self.render_to_response(context)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EditProfileClientView(LoginRequiredMixin, TemplateView):
    template_name = "moderations/profile_edit_client.html"

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        profile_id = kwargs.get("pk")
        profile = get_object_or_404(Profile, id=profile_id)

        # Проверяем, есть ли у пользователя права редактирования чужих профилей
        can_edit = request.user.is_superuser or request.user.has_perm(
            "useraccount.change_profile"
        )

        if not (can_edit or request.user == profile.user):
            return HttpResponseForbidden(
                "У вас нет прав для редактирования этого профиля."
            )

        initial_data = {
            "birthday": profile.birthday.strftime("%Y-%m-%d")
            if profile.birthday
            else None
        }
        form = UserProfileForm(instance=profile, initial=initial_data)
        context = self.get_context_data(
            form=form, title="Личные данные", profile=profile
        )
        return self.render_to_response(context)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        profile_id = kwargs.get("pk")
        profile = get_object_or_404(Profile, id=profile_id)

        # Проверяем, может ли пользователь редактировать профиль
        can_edit = request.user.is_superuser or request.user.has_perm(
            "useraccount.change_profile"
        )

        if not (can_edit or request.user == profile.user):
            return HttpResponseForbidden(
                "У вас нет прав для редактирования этого профиля."
            )

        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("moderation:edit_profile_client", pk=profile_id)

        context = self.get_context_data(
            form=form, title="Личные данные", profile=profile
        )
        return self.render_to_response(context)


@method_decorator(login_required(login_url="useraccount:login"), name="dispatch")
class UserDetailView(TemplateView):
    template_name = "moderations/users_detail.html"

    def get_context_data(self, user_id, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(Profile, id=user_id)
        context["users"] = user
        return context


"""HTMX"""


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class UserListHtmxView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = "moderations/htmx/user.html"
    context_object_name = "users"
    paginate_by = 50

    def get_queryset(self):
        queryset = Profile.objects.filter(type=2)
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(Q(username__icontains=search_query))
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        context = self.get_context_data(object_list=queryset)

        if request.headers.get("HX-Request") == "true":
            return render(request, "moderations/htmx/user_list_partial.html", context)
        return super().get(request, *args, **kwargs)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ClientListHtmxView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = "moderations/htmx/client.html"
    context_object_name = "users"
    paginate_by = 50

    def get_queryset(self):
        queryset = Profile.objects.filter(type=1)
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(Q(username__icontains=search_query))
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        context = self.get_context_data(object_list=queryset)

        if request.headers.get("HX-Request") == "true":
            return render(request, "moderations/htmx/user_list_partial.html", context)
        return super().get(request, *args, **kwargs)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PartnerListHtmxView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = "moderations/htmx/partner.html"
    context_object_name = "users"
    paginate_by = 50

    def get_queryset(self):
        queryset = Profile.objects.filter(type=3)
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(Q(username__icontains=search_query))
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        context = self.get_context_data(object_list=queryset)

        if request.headers.get("HX-Request") == "true":
            return render(request, "moderations/htmx/user_list_partial.html", context)
        return super().get(request, *args, **kwargs)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class KnowledgePage(LoginRequiredMixin, ListView):
    model = Documentations
    template_name = "moderations/knowelege.html"
    context_object_name = "knowelege"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        knowelege = Documentations.objects.all()
        if user.type == 1:
            knowelege = knowelege.filter(type=1)
        elif user.type == 2:
            knowelege = knowelege.filter(type=2)
        elif user.type == 3:
            knowelege = knowelege.filter(type=3)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            knowelege = knowelege.filter(name__icontains=search_name)

        # Пагинация
        paginator = Paginator(knowelege, 1)
        page = self.request.GET.get("page")
        try:
            knowelege_list = paginator.page(page)
        except PageNotAnInteger:
            knowelege_list = paginator.page(1)
        except EmptyPage:
            knowelege_list = paginator.page(paginator.num_pages)

        context["knowelege_list"] = knowelege_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = knowelege_list
        context["files"] = DocumentationsMedia.objects.filter(
            documentations__in=knowelege_list
        )
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class WithdrawPage(LoginRequiredMixin, TemplateView):
    template_name = "moderations/withdraw.html"
    model = Withdrawal
    context_object_name = "withdraw"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        withdraw = Withdrawal.objects.filter(user=user).order_by("-pk")

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            withdraw = withdraw.filter(pk=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            withdraw = withdraw.filter(type=search_type)

        user_id = self.request.GET.get("user_id", "")
        if user_id:
            withdraw = withdraw.filter(user__id=user_id)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                withdraw = withdraw.filter(create=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(withdraw, 10)  # 20 элементов на страницу
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
        context["cards"] = user.cardowner.first()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class WithdrawCreateView(LoginRequiredMixin, CreateView):
    model = Withdrawal
    form_class = WithdrawForm
    template_name = "moderations/iframe/withdraw_form.html"
    success_url = reverse_lazy("moderation:withdraw")
    context_object_name = "withdraw"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["balance"] = user.balance
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class WithdrawAllPage(LoginRequiredMixin, TemplateView):
    template_name = "moderations/withdraw.html"
    model = Withdrawal
    context_object_name = "withdraw"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        withdraw = Withdrawal.objects.order_by("-pk").all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            withdraw = withdraw.filter(pk=search_id)

        search_type = self.request.GET.get("search_type", "")
        if search_type:
            withdraw = withdraw.filter(type=search_type)

        user_id = self.request.GET.get("user_id", "")
        if user_id:
            withdraw = withdraw.filter(user__id=user_id)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                withdraw = withdraw.filter(create=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(withdraw, 10)  # 20 элементов на страницу
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
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CardsCreateView(LoginRequiredMixin, CreateView):
    model = Cards
    form_class = CardsForm
    template_name = "moderations/iframe/cards_form.html"
    success_url = reverse_lazy("moderation:withdraw")
    context_object_name = "cards"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CardsUpdateView(LoginRequiredMixin, UpdateView):
    model = Cards
    form_class = CardsForm
    template_name = "moderations/iframe/cards_form.html"
    success_url = reverse_lazy("moderation:withdraw")
    context_object_name = "cards"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@csrf_exempt
@login_required
def update_location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            location = data.get("location", None)

            if location:
                request.user.location = location
                request.user.save()
                return JsonResponse(
                    {"status": "success", "message": "Местоположение обновлено"}
                )
            else:
                return JsonResponse(
                    {"status": "error", "message": "Местоположение не предоставлено"},
                    status=400,
                )

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse(
        {"status": "error", "message": "Метод не поддерживается"}, status=405
    )


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ScheduleList(View):
    def get(self, request, user_id):
        schedules = Schedule.objects.filter(user_id=user_id)

        # Фильтруем события на ближайшие 5 дней
        upcoming_schedules = schedules.filter(
            data_start__range=[now().date(), (now() + timedelta(days=5)).date()]
        ).order_by("data_start")

        # Создаём список событий с CSS классами и добавляем id
        events = [
            {
                "id": schedule.id,  # Добавляем ID события
                "title": schedule.name,
                "start": f"{schedule.data_start}T{schedule.time_start}",
                "end": f"{schedule.data_end}T{schedule.time_end}",
                "description": schedule.description,
                "className": schedule.get_pagetype_class(),  # Используем метод get_pagetype_class()
            }
            for schedule in schedules
        ]

        categories = Schedule.get_pagetype_choices()

        return render(
            request,
            "moderations/schedule_calendar.html",
            {
                "events": json.dumps(events),
                "categories": categories,
                "upcoming_events": upcoming_schedules,
            },
        )


class ScheduleCreateView(View):
    def post(self, request):
        # Получаем данные из JSON тела запроса
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data."}, status=400
            )

        # Извлекаем данные
        title = data.get("title")
        category = data.get("category")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        description = data.get("description")
        user_id = data.get("user_id")  # Получаем user_id

        # Проверяем корректность дат
        start_datetime = parse_datetime(f"{start_date} {start_time}")
        end_datetime = parse_datetime(f"{end_date} {end_time}")

        if not start_datetime or not end_datetime:
            return JsonResponse(
                {"status": "error", "message": "Invalid date or time format"},
                status=400,
            )

        # Определяем пользователя
        if user_id:
            try:
                user = Profile.objects.get(id=user_id)
            except Profile.DoesNotExist:
                return JsonResponse(
                    {"status": "error", "message": "User not found"}, status=400
                )
        else:
            user = request.user  # Используем текущего пользователя

        # Создаем событие
        event = Schedule.objects.create(
            name=title,
            description=description,
            data_start=start_datetime.date(),
            data_end=end_datetime.date(),
            time_start=start_datetime.time(),
            time_end=end_datetime.time(),
            pagetype=category,
            user=user,  # Добавляем пользователя
        )

        return JsonResponse(
            {"status": "success", "message": "Event successfully created!"}
        )


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ExtendedSiteListView(ListView):
    model = ExtendedSite
    template_name = "moderations/extended_site_list.html"
    context_object_name = "extended_sites"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        site_ids = [es.site_id for es in context["extended_sites"]]

        # HomePage
        # HomePage
        homepages = HomePage.objects.filter(site__id__in=site_ids).distinct()
        homepage_map = {}
        for homepage in homepages:
            site = homepage.site
            homepage_map.setdefault(site.id, []).append(homepage)
        context["homepage_map"] = homepage_map

        # SettingsGlobale (предположим, OneToOne с Site)
        settings_map = {
            sg.site_id: sg
            for sg in SettingsGlobale.objects.filter(site_id__in=site_ids)
        }
        context["settings_map"] = settings_map

        # ContactPage (предположим, ForeignKey к Site)
        contact_map = {}
        for contact in ContactPage.objects.filter(site_id__in=site_ids):
            contact_map.setdefault(contact.site_id, []).append(contact)
        context["contact_map"] = contact_map

        # AboutPage (предположим, ForeignKey к Site)
        about_map = {}
        for about in AboutPage.objects.filter(site_id__in=site_ids):
            about_map.setdefault(about.site_id, []).append(about)
        context["about_map"] = about_map

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ExtendedSiteCreateView(CreateView):
    model = ExtendedSite
    form_class = ExtendedSiteForm
    template_name = "moderations/extended_site_form.html"
    success_url = reverse_lazy("moderation:extended_site_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category_id = self.request.GET.get("category")
        context["selected_category"] = (
            int(category_id) if category_id and category_id.isdigit() else None
        )

        context["all_categories"] = ThemesCastegorys.objects.filter(publishet=True)

        themes_qs = Themes.objects.filter(publishet=True)
        if category_id and category_id.isdigit():
            themes_qs = themes_qs.filter(categorys_id=category_id)

        context["filtered_themes"] = themes_qs

        # Выбранные темы из POST-запроса (если есть)
        if self.request.method == "POST":
            context["selected_templates"] = self.request.POST.getlist("templates")
        else:
            context["selected_templates"] = []

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ExtendedSiteUpdateView(UpdateView):
    model = ExtendedSite
    form_class = ExtendedSiteForm
    template_name = "moderations/extended_site_form.html"
    success_url = reverse_lazy("moderation:extended_site_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category_id = self.request.GET.get("category")
        context["selected_category"] = (
            int(category_id) if category_id and category_id.isdigit() else None
        )

        context["all_categories"] = ThemesCastegorys.objects.filter(publishet=True)

        themes_qs = Themes.objects.filter(publishet=True)
        if category_id and category_id.isdigit():
            themes_qs = themes_qs.filter(categorys_id=category_id)

        context["filtered_themes"] = themes_qs

        # Выбранные темы из POST-запроса (если есть)
        if self.request.method == "POST":
            context["selected_templates"] = self.request.POST.getlist("templates")
        else:
            context["selected_templates"] = []

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ExtendedSiteDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:extended_site_list")

    def post(self, request):
        data = json.loads(request.body)
        site_ids = data.get("site_ids", [])
        if site_ids:
            ExtendedSite.objects.filter(id__in=site_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(
    csrf_exempt, name="dispatch"
)  # Отключает CSRF, если не используется Django Forms
class ScheduleUpdateView(View):
    # Метод для получения данных события
    def get(self, request, schedule_id):
        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Event not found"}, status=404
            )

        response_data = {
            "id": schedule.id,
            "title": schedule.name,
            "category": schedule.pagetype,
            "start_date": schedule.data_start,
            "end_date": schedule.data_end,
            "start_time": schedule.time_start,
            "end_time": schedule.time_end,
            "description": schedule.description,
            "user_id": schedule.user_id,
        }
        return JsonResponse({"status": "success", "event": response_data})

    # Метод для обновления данных события (POST + PUT)
    def post(self, request, schedule_id):
        return self.update_event(request, schedule_id)

    def put(self, request, schedule_id):  # ✅ Добавляем поддержку PUT
        return self.update_event(request, schedule_id)

    def update_event(self, request, schedule_id):
        try:
            schedule = Schedule.objects.get(id=schedule_id)
        except Schedule.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Event not found"}, status=404
            )

        data = json.loads(request.body)

        schedule.name = data.get("title", schedule.name)
        schedule.pagetype = data.get("category", schedule.pagetype)
        schedule.data_start = data.get("start_date", schedule.data_start)
        schedule.data_end = data.get("end_date", schedule.data_end)
        schedule.time_start = data.get("start_time", schedule.time_start)
        schedule.time_end = data.get("end_time", schedule.time_end)
        schedule.description = data.get("description", schedule.description)
        schedule.user_id = data.get("user_id", schedule.user_id)

        schedule.save()

        response_data = {
            "id": schedule.id,
            "title": schedule.name,
            "category": schedule.pagetype,
            "start_date": schedule.data_start,
            "end_date": schedule.data_end,
            "start_time": schedule.time_start,
            "end_time": schedule.time_end,
            "description": schedule.description,
            "user_id": schedule.user_id,
        }

        return JsonResponse(
            {
                "status": "success",
                "message": "Event updated successfully!",
                "event": response_data,
            }
        )


class ScheduleDeleteView(View):
    def post(self, request, schedule_id):
        try:
            schedule = Schedule.objects.get(id=schedule_id)
            schedule.delete()
            return JsonResponse(
                {"status": "success", "message": "Событие успешно удалено!"}
            )
        except Schedule.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Событие не найдено."})


"""Объявления"""


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class Complaints(LoginRequiredMixin, ListView):
    template_name = "moderations/complaints.html"
    model = Complaint
    context_object_name = "complaint"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Complaint.objects.all()

        # 🔐 Фильтрация по владельцу или помощнику производителя
        if user.type in [2, 3]:
            queryset = queryset.filter(
                Q(products__manufacturers__owner=user) |
                Q(products__manufacturers__assistant=user)
            ).distinct()

        return queryset.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        complaints = self.get_queryset()

        # Фильтрация по полям из GET
        type_value = self.request.GET.get("type")
        booking_value = self.request.GET.get("booking")
        advertisement_value = self.request.GET.get("advertisement")
        author_value = self.request.GET.get("author")
        create_value = self.request.GET.get("create")
        description_value = self.request.GET.get("description")

        if type_value and type_value.isdigit():
            complaints = complaints.filter(type=int(type_value))

        if booking_value and booking_value.isdigit():
            complaints = complaints.filter(booking_id=int(booking_value))

        if advertisement_value and advertisement_value.isdigit():
            complaints = complaints.filter(advertisement_id=int(advertisement_value))

        if author_value and author_value.isdigit():
            complaints = complaints.filter(author_id=int(author_value))

        if create_value:
            try:
                create_date = datetime.strptime(create_value, "%Y-%m-%d").date()
                complaints = complaints.filter(create__date=create_date)
            except ValueError:
                pass

        if description_value:
            complaints = complaints.filter(description__icontains=description_value)

        # Пагинация
        paginator = Paginator(complaints, self.paginate_by)
        page = self.request.GET.get("page")
        try:
            complaints_list = paginator.page(page)
        except PageNotAnInteger:
            complaints_list = paginator.page(1)
        except EmptyPage:
            complaints_list = paginator.page(paginator.num_pages)

        context["complaints_list"] = complaints_list
        context["paginator"] = paginator
        context["page_obj"] = complaints_list
        context["filter_params"] = self.request.GET.copy()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ComplaintsUpdateView(LoginRequiredMixin, UpdateView):
    model = Complaint
    form_class = ComplaintForm
    template_name = "moderations/сomplaint_form.html"
    success_url = reverse_lazy("moderation:complaints")
    context_object_name = "complaint"  # Должно быть в единственном числе
    pk_url_kwarg = "pk"  # Указываем, что pk берётся из URL

    def form_valid(self, form):
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ReviewListView(ListView):
    model = Reviews
    template_name = "moderations/reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Reviews.objects.all()

        # 🔐 Фильтрация по владельцу или помощнику производителя
        if user.type in [2, 3]:
            queryset = queryset.filter(
                Q(product__manufacturers__owner=user) |
                Q(product__manufacturers__assistant=user)
            ).distinct()

        return queryset.order_by("-create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reviews = self.get_queryset()

        # Фильтры
        publishet = self.request.GET.get("publishet")
        text = self.request.GET.get("text")
        starvalue = self.request.GET.get("starvalue")
        review_id = self.request.GET.get("id")
        author_review = self.request.GET.get("author_review")
        create = self.request.GET.get("create")

        if publishet is not None:
            reviews = reviews.filter(publishet=publishet.lower() in ["true", "1", "yes"])

        if text:
            reviews = reviews.filter(text__icontains=text)

        if starvalue and starvalue.isdigit():
            reviews = reviews.filter(starvalue=int(starvalue))

        if review_id:
            reviews = reviews.filter(id__icontains=review_id)

        if author_review and author_review.isdigit():
            reviews = reviews.filter(author_id=int(author_review))

        if create:
            try:
                create_date = datetime.strptime(create, "%Y-%m-%d").date()
                reviews = reviews.filter(create__date=create_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(reviews, self.paginate_by)
        page = self.request.GET.get("page")
        try:
            reviews_list = paginator.page(page)
        except PageNotAnInteger:
            reviews_list = paginator.page(1)
        except EmptyPage:
            reviews_list = paginator.page(paginator.num_pages)

        context["reviews_list"] = reviews_list
        context["paginator"] = paginator
        context["page_obj"] = reviews_list
        context["filter_params"] = self.request.GET.copy()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ReviewsDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:reviews")

    def post(self, request):
        data = json.loads(request.body)
        review_ids = data.get("review_ids", [])
        if review_ids:
            Reviews.objects.filter(id__in=review_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# теги
#
# @login_required()
# def create_advertisement_tag(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         slug = request.POST.get('slug')
#         description = request.POST.get('description')
#         title = request.POST.get('title')
#         content = request.POST.get('content')
#         parent_id = request.POST.get('parent')
#         cover = request.FILES.get('cover')
#         icon = request.FILES.get('icon')
#         image = request.FILES.get('image')
#         site_id = request.POST.get('site')
#
#         tag = TagsProducts.objects.create(
#             name=name,
#             slug=slug,
#             description=description,
#             title=title,
#             content=content,
#             parent_id=parent_id,
#             cover=cover,
#             icon=icon,
#             image=image,
#             site_id=1,
#         )
#
#         return JsonResponse({'success': True, 'tag_id': tag.id})
#
#     return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
#
#
# def advertisement_tag_list(request):
#     tags = TagsProducts.objects.all().values('id', 'name')  # Получаем нужные поля
#     return JsonResponse({'tags': list(tags)})
#
# @method_decorator(login_required(login_url='moderation:login'), name='dispatch')
# class TagsProductsSettings(LoginRequiredMixin, ListView):
#     template_name = 'moderations/advertisement_tags_settings.html'
#     model = TagsProducts
#     context_object_name = 'advertisement_tags_settings'
#     paginate_by = 10
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         tags = TagsProducts.objects.all()
#
#
#         search_name = self.request.GET.get('search_name', '')
#         if search_name:
#             tags = tags.filter(name__icontains=search_name)
#
#         search_tag = self.request.GET.get('search_tag', '')
#         if search_tag:
#             tags = tags.filter(parent__id=search_tag)
#
#
#         # Пагинация
#         paginator = Paginator(tags, 10)  # 20 элементов на страницу
#         page = self.request.GET.get('page')
#         try:
#             tags_list = paginator.page(page)
#         except PageNotAnInteger:
#             tags_list = paginator.page(1)
#         except EmptyPage:
#             tags_list = paginator.page(paginator.num_pages)
#
#         context['tags_list'] = tags_list  # Передаем отфильтрованные задачи
#         context['paginator'] = paginator
#         context['page_obj'] = tags_list
#         return context


@login_required()
def save_advertisement_tags(request, slug):
    # Получаем объект блога по slug
    blog = get_object_or_404(Products, slug=slug)

    if request.method == "GET":
        tags = request.GET.get("tags", "")
        if tags:
            tag_list = tags.split(",")
            blog.tag.clear()
            for tag_id in tag_list:
                tag = get_object_or_404(TagsBlogs, id=tag_id)
                blog.tag.add(tag)

            return JsonResponse(
                {"status": "success", "message": "Categories saved successfully."}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "No categories provided."}, status=400
            )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid request method."}, status=400
        )


@login_required()
def save_advertisement_categories(request, slug):
    # Получаем объект блога по slug
    blog = get_object_or_404(Products, slug=slug)

    if request.method == "GET":
        categories = request.GET.get("categories", "")
        if categories:
            category_list = categories.split(",")
            blog.category.clear()
            for category_id in category_list:
                category = get_object_or_404(Categories, id=category_id)
                blog.category.add(category)

            return JsonResponse(
                {"status": "success", "message": "Categories saved successfully."}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "No categories provided."}, status=400
            )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid request method."}, status=400
        )


#
# @method_decorator(login_required(login_url='moderation:login'), name='dispatch')
# class TagsProductsCreateView(LoginRequiredMixin, CreateView):
#     model = TagsProducts
#     form_class = TagsProductsForm
#     template_name = 'moderations/advertisement_tags_form.html'
#     success_url = reverse_lazy('moderation:advertisement_tags_settings')
#     context_object_name = 'tags'
#
#     def form_valid(self, form):
#         form.save()
#         return super().form_valid(form)
#
#
# @method_decorator(login_required(login_url='moderation:login'), name='dispatch')
# class TagsProductsUpdateView(LoginRequiredMixin, UpdateView):
#     model = TagsProducts
#     form_class = TagsProductsForm
#     template_name = 'moderations/advertisement_tags_form.html'
#     success_url = reverse_lazy('moderation:advertisement_tags_settings')
#     context_object_name = 'tags'
#
#     def form_valid(self, form):
#         form.save()
#         return super().form_valid(form)
#
#
# @method_decorator(login_required(login_url='moderation:login'), name='dispatch')
# class TagsProductsDeleteView(LoginRequiredMixin, View):
#     success_url = reverse_lazy('moderation:advertisement_tags_settings')
#
#     def post(self, request):
#         data = json.loads(request.body)
#         tagsblogs_ids = data.get('tagsblogs_ids', [])
#         if tagsblogs_ids:
#             TagsProducts.objects.filter(id__in=tagsblogs_ids).delete()
#         return JsonResponse({'status': 'success', 'redirect': self.success_url})

# - теги


@login_required()
def save_advertisement_categories(request, slug):
    # Получаем объект блога по slug
    blog = get_object_or_404(Products, slug=slug)

    if request.method == "GET":
        categories = request.GET.get("categories", "")
        if categories:
            category_list = categories.split(",")
            blog.category.clear()
            for category_id in category_list:
                category = get_object_or_404(Categories, id=category_id)
                blog.category.add(category)

            return JsonResponse(
                {"status": "success", "message": "Categories saved successfully."}
            )
        else:
            return JsonResponse(
                {"status": "error", "message": "No categories provided."}, status=400
            )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid request method."}, status=400
        )


@login_required()
def create_category_advertisement(request):
    if request.method == "POST":
        name = request.POST.get("name")
        slug = request.POST.get("slug")
        description = request.POST.get("description")
        title = request.POST.get("title")
        content = request.POST.get("content")
        parent_id = request.POST.get("parent")
        cover = request.FILES.get("cover")
        icon = request.FILES.get("icon")
        image = request.FILES.get("image")
        site_id = request.POST.get("site")

        category = Categories.objects.create(
            name=name,
            slug=slug,
            description=description,
            title=title,
            content=content,
            parent_id=parent_id,
            cover=cover,
            icon=icon,
            image=image,
            site_id=1,
        )

        return JsonResponse({"success": True, "category_id": category.id})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


def advertisement_category_list(request):
    categories = Categories.objects.all().values("id", "name")  # Получаем нужные поля
    return JsonResponse({"categories": list(categories)})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategoryProducts(LoginRequiredMixin, ListView):
    template_name = "moderations/advertisement_categorys_settings.html"
    model = Categories
    context_object_name = "categorys_settings"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categorys = Categories.objects.all()

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            categorys = categorys.filter(name__icontains=search_name)

        search_category = self.request.GET.get("search_category", "")
        if search_category:
            categorys = categorys.filter(parent__id=search_category)

        # Пагинация
        paginator = Paginator(categorys, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            categorys_list = paginator.page(page)
        except PageNotAnInteger:
            categorys_list = paginator.page(1)
        except EmptyPage:
            categorys_list = paginator.page(paginator.num_pages)

        context["categorys_list"] = categorys_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = categorys_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategoriesCreateView(LoginRequiredMixin, CreateView):
    model = Categories
    form_class = CategoriesForm
    template_name = "moderations/advertisement_categorys_form.html"
    success_url = reverse_lazy("moderation:categorys_product_settings")
    context_object_name = "categorys"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategoriesUpdateView(LoginRequiredMixin, UpdateView):
    model = Categories
    form_class = CategoriesForm
    template_name = "moderations/advertisement_categorys_form.html"
    success_url = reverse_lazy("moderation:categorys_product_settings")
    context_object_name = "categorys"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CategoriesDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:categorys_product_settings")

    def post(self, request):
        data = json.loads(request.body)
        categorysblogs_ids = data.get("categorysblogs_ids", [])
        if categorysblogs_ids:
            Categories.objects.filter(id__in=categorysblogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VacancyResponse(LoginRequiredMixin, ListView):
    template_name = "moderations/vacances_aplication.html"
    model = VacancyResponse
    context_object_name = "vacancesaplication"
    paginate_by = 10


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class StatusPaymentListView(ListView):
    model = StatusPayment
    template_name = "moderations/statuspayment_list.html"
    context_object_name = "payments"
    paginate_by = 10

    def get_queryset(self):
        queryset = StatusPayment.objects.all().order_by("-created_at")

        # Поиск по дате
        search_date = self.request.GET.get("search_date")
        if search_date:
            try:
                search_date_obj = timezone.datetime.strptime(
                    search_date, "%Y-%m-%d"
                ).date()
                queryset = queryset.filter(created_at__date=search_date_obj)
            except ValueError:
                pass

        # Поиск по статусу
        search_status = self.request.GET.get("search_status")
        if search_status:
            queryset = queryset.filter(status=search_status)

        # Поиск по сумме
        search_amount = self.request.GET.get("search_amount")
        if search_amount:
            try:
                amount = float(search_amount)
                queryset = queryset.filter(amount=amount)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_tasks = Task.objects.select_related("payment")
        all_leads = Lead.objects.prefetch_related("payment")

        payment_data = []
        for payment in context["payments"]:
            tasks = [task for task in all_tasks if task.payment_id == payment.id]
            leads = [lead for lead in all_leads if payment in lead.payment.all()]
            payment_data.append(
                {
                    "payment": payment,
                    "tasks": tasks,
                    "leads": leads,
                }
            )

        context["payment_data"] = payment_data

        # Для отображения текущих фильтров в шаблоне
        context["search_date"] = self.request.GET.get("search_date", "")
        context["search_status"] = self.request.GET.get("search_status", "")
        context["search_amount"] = self.request.GET.get("search_amount", "")

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class StatusPaymentDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:statuspayment_list")

    def post(self, request):
        data = json.loads(request.body)
        blogs_ids = data.get("blogs_ids", [])
        if blogs_ids:
            StatusPayment.objects.filter(id__in=blogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


class AjaxStatusPaymentCreateView(View):
    def post(self, request, *args, **kwargs):
        form = StatusPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({"status": "success"})
        return JsonResponse({"status": "error", "errors": form.errors})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class Vacances(LoginRequiredMixin, ListView):
    template_name = "moderations/vacances.html"
    model = Vacancy
    context_object_name = "vacances"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vacances = Vacancy.objects.all().order_by("-create")

        search_title = self.request.GET.get("search_title", "")
        if search_title:
            vacances = vacances.filter(name__icontains=search_title)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                vacances = vacances.filter(create__date=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(vacances, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            vacances_list = paginator.page(page)
        except PageNotAnInteger:
            vacances_list = paginator.page(1)
        except EmptyPage:
            vacances_list = paginator.page(paginator.num_pages)

        context["vacances_list"] = vacances_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = vacances_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VacancesCreateView(LoginRequiredMixin, CreateView):
    model = Vacancy
    form_class = VacancyForm
    template_name = "moderations/vacancys_form.html"
    success_url = reverse_lazy("moderation:vacances")
    context_object_name = "vacances"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VacancesUpdateView(LoginRequiredMixin, UpdateView):
    model = Vacancy
    form_class = VacancyForm
    template_name = "moderations/vacancys_form.html"
    success_url = reverse_lazy("moderation:vacances")
    context_object_name = "vacances"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VacancesDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:vacances")

    def post(self, request):
        data = json.loads(request.body)
        vacances_ids = data.get("vacances_ids", [])
        if vacances_ids:
            Vacancy.objects.filter(id__in=vacances_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class OrdersView(ListView):
    template_name = "moderations/orders.html"
    model = Order
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.all()

        # 🔒 Фильтрация по владельцу/ассистенту производителя
        if user.type in [2, 3]:
            queryset = queryset.filter(
                Q(selectedproduct__product__manufacturers__owner=user) |
                Q(selectedproduct__product__manufacturers__assistant=user)
            ).distinct()

        return queryset.order_by("-created_timestamp")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = self.get_queryset()

        filter_fields = [
            "reviews",
            "type",
            "status",
            "phone_number",
            "customer_name",
            "customer_surname",
            "customer_email",
            "sflat",
            "sfloor",
            "porch",
            "user_comment",
            "requires_delivery",
            "delivery_address",
            "longitude",
            "latitude",
            "city",
            "adress",
            "amount",
            "delivery_price",
            "all_amount",
            "key",
            "purchase_url",
            "site__id",
            "payload",
            "is_payload_set",
            "claim_id",
            "is_claim_id_set",
            "mail_send",
            "user__id",
        ]

        for field in filter_fields:
            value = self.request.GET.get(field, "")
            if value != "":
                if field in [
                    "reviews",
                    "requires_delivery",
                    "is_payload_set",
                    "is_claim_id_set",
                    "mail_send",
                ]:
                    orders = orders.filter(**{field: value.lower() in ["1", "true", "yes"]})
                elif field in ["type", "status", "site__id", "user__id"]:
                    orders = orders.filter(**{field: int(value)})
                elif field in ["amount", "delivery_price", "all_amount"]:
                    try:
                        orders = orders.filter(**{field: int(value)})
                    except ValueError:
                        pass
                else:
                    orders = orders.filter(**{f"{field}__icontains": value})

        # Фильтрация по дате создания
        search_date = self.request.GET.get("created_timestamp", "")
        if search_date:
            try:
                date_obj = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                orders = orders.filter(created_timestamp__date=date_obj)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(orders, self.paginate_by)
        page = self.request.GET.get("page")
        try:
            orders_page = paginator.page(page)
        except PageNotAnInteger:
            orders_page = paginator.page(1)
        except EmptyPage:
            orders_page = paginator.page(paginator.num_pages)

        context["orders"] = orders_page
        context["paginator"] = paginator
        context["page_obj"] = orders_page
        context["filter_params"] = self.request.GET.copy()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class OrderCreateView(View):
    def get(self, request, *args, **kwargs):
        # Создаем заказ, можно указать нужные поля по умолчанию
        order = (
            Order.objects.create()
        )  # при необходимости передай user=request.user и т.п.

        # Перенаправляем на страницу редактирования созданного заказа
        return redirect("moderation:order_edit", pk=order.pk)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class OrderUpdateView(UpdateView):
    model = Order
    form_class = OrderForm
    context_object_name = "order"
    template_name = "moderations/order_form.html"
    success_url = reverse_lazy("moderation:orders")

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get("pk")
        order = get_object_or_404(queryset, pk=pk)
        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["selectedproduct_formset"] = SelectedProductFormSet(
                self.request.POST, queryset=self.object.selectedproduct.all()
            )
        else:
            context["selectedproduct_formset"] = SelectedProductFormSet(
                queryset=self.object.selectedproduct.all()
            )
        context["manufacturer"] = getattr(self.request.user, "manufacturers", None)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["selectedproduct_formset"]
        if formset.is_valid():
            self.object = form.save()
            selected_products = formset.cleaned_data

            # Очистка текущих связей
            self.object.selectedproduct.clear()

            for product_form in formset:
                if product_form.cleaned_data and not product_form.cleaned_data.get(
                        "DELETE", False
                ):
                    selected_product = product_form.save()
                    self.object.selectedproduct.add(selected_product)

            messages.success(self.request, "Заказ успешно обновлен.")
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, "Ошибка при обновлении заказа.")
            return self.render_to_response(self.get_context_data(form=form))


@require_POST
@login_required
def add_selected_product(request):
    order_id = request.POST.get("order_id")
    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 0))
    amount = request.POST.get("amount", "0")
    status = int(request.POST.get("status", 1))

    try:
        product = Products.objects.get(id=product_id)
    except Products.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "Продукт не найден"}, status=404
        )

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"success": False, "error": "Заказ не найден"}, status=404)

    selected_product = SelectedProduct.objects.create(
        product=product,
        quantity=quantity,
        amount=amount,
        status=status,
        user=request.user,
    )

    # ✅ Привязка к заказу
    order.selectedproduct.add(selected_product)

    return JsonResponse({"success": True, "id": str(selected_product.id)})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class OrderDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:orders")

    def post(self, request):
        data = json.loads(request.body)
        blogs_ids = data.get("blogs_ids", [])
        if blogs_ids:
            Order.objects.filter(id__in=blogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class AssetListView(ListView):
    model = Asset
    template_name = "moderations/asset_list.html"
    context_object_name = "assets"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        name_query = self.request.GET.get("name", "").strip()
        inventory_query = self.request.GET.get("inventory_number", "").strip()

        if name_query and inventory_query:
            queryset = queryset.filter(
                Q(name__icontains=name_query)
                & Q(inventory_number__icontains=inventory_query)
            )
        elif name_query:
            queryset = queryset.filter(name__icontains=name_query)
        elif inventory_query:
            queryset = queryset.filter(inventory_number__icontains=inventory_query)

        queryset = queryset.order_by("id")

        print(f"Filtered queryset ({queryset.count()} items):")
        for obj in queryset:
            print(
                f" - id={obj.id}, name={obj.name}, inventory_number={obj.inventory_number}"
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаём значения поиска в контекст, чтобы они сохранились в шаблоне
        context["name_query"] = self.request.GET.get("name", "")
        context["inventory_query"] = self.request.GET.get("inventory_number", "")
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class AssetUpdateView(UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "moderations/asset_edit.html"
    success_url = reverse_lazy("moderation:asset_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.object
        context["maintenance_records"] = asset.maintenance_records.order_by("-date")
        context["usage_records"] = asset.usage_records.order_by("-taken_at")
        return context


@login_required
def asset_usage_list(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    usage_records = asset.usage_records.order_by("-taken_at")
    return render(
        request, "moderations/include/usage_list.html", {"usage_records": usage_records}
    )


@login_required
@require_POST
def toggle_usage_active(request, usage_id):
    usage = get_object_or_404(AssetUsage, id=usage_id)
    # Переключаем значение is_active
    usage.is_active = not usage.is_active
    usage.save()
    return JsonResponse({"success": True, "is_active": usage.is_active})


@login_required
def asset_maintenance_list(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    maintenance_records = asset.maintenance_records.order_by("-date")
    return render(
        request,
        "moderations/include/maintenance_list.html",
        {"maintenance_records": maintenance_records},
    )


@login_required
@require_POST
def asset_usage_create(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    user_id = request.POST.get("user")
    taken_at = request.POST.get("taken_at")
    purpose = request.POST.get("purpose", "")
    # Тут надо добавить валидацию и обработку ошибок
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.filter(id=user_id).first()  # Можно добавить проверку
    AssetUsage.objects.create(
        asset=asset, user=user, taken_at=taken_at, purpose=purpose
    )
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def asset_maintenance_create(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    date = request.POST.get("date")
    performed_by = request.POST.get("performed_by")
    description = request.POST.get("description")
    next_due_date = request.POST.get("next_due_date") or None
    if next_due_date == "":
        next_due_date = None
    Maintenance.objects.create(
        asset=asset,
        date=date,
        performed_by=performed_by,
        description=description,
        next_due_date=next_due_date,
    )
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def asset_usage_delete(request, usage_id):
    usage = get_object_or_404(AssetUsage, id=usage_id)
    usage.delete()
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def asset_maintenance_delete(request, maintenance_id):
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    maintenance.delete()
    return JsonResponse({"status": "ok"})


User = get_user_model()


@login_required
def user_list_json(request):
    users = User.objects.all().values("id", "username")
    return JsonResponse(list(users), safe=False)


class AssetCreateAndRedirectView(View):
    def get(self, request, *args, **kwargs):
        asset = Asset.objects.create(
            name="",
            inventory_number=str(uuid.uuid4())[:8],  # например, "a1b2c3d4"
        )
        return redirect("moderation:asset_edit", pk=asset.pk)


@method_decorator(csrf_exempt, name='dispatch')
class ProductCopyView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            product_ids = data.get('blogs_ids', [])
            copied_products = []

            for pid in product_ids:
                try:
                    original = Products.objects.get(id=pid)
                except Products.DoesNotExist:
                    continue

                # Создаем копию объекта
                original.pk = None  # сбрасываем первичный ключ
                original.article = original.generate_unique_article()  # генерируем новый уникальный артикул
                original.slug = None  # сбрасываем slug, чтобы Django создал новый или оставляем None
                original.name = f"{original.name} (Копия)"
                original.save()  # сохраняем копию

                # Устанавливаем связи ManyToMany заново
                original.category.set(Products.objects.get(id=pid).category.all())
                original.manufacturers.set(Products.objects.get(id=pid).manufacturers.all())
                original.site.set(Products.objects.get(id=pid).site.all())

                copied_products.append({
                    'id': str(original.id),
                    'name': original.name,
                })

            return JsonResponse({'status': 'success', 'copied_products': copied_products})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


class ProductsCheckView(View):
    def get(self, request, *args, **kwargs):
        products = Products.objects.all()

        # Проходим по продуктам и проверяем условия
        products_with_variable = {}
        attributes_by_variable = {}

        for product in products:
            if product.type != 1:
                variable = ProductsVariable.objects.filter(
                    products=product, defaultposition=True
                ).first()
                if not variable:
                    variable = ProductsVariable.objects.filter(products=product).first()

                if variable:
                    products_with_variable[product.id] = variable
                    variation_slug = variable.slug

            for product_variable in product.productsvariable_set.all():
                for attribute in product_variable.attribute.all():
                    variable = attribute.variable
                    if variable not in attributes_by_variable:
                        attributes_by_variable[variable] = set()
                    attributes_by_variable[variable].add(attribute)

            for variable in attributes_by_variable:
                attributes_by_variable[variable] = list(attributes_by_variable[variable])


        context = {'products': products,'products_with_variable':products_with_variable,'attributes_by_variable':attributes_by_variable}
        return render(request, 'moderations/offline_cart.html', context)


@method_decorator(csrf_exempt, name='dispatch')
class CheckPaymentStatusView(View):
    def post(self, request):
        order_id = request.POST.get('order_id')
        order_key = request.POST.get('order_key')

        # Проверка, зарегистрирован ли пользователь
        user = request.user
        if user.is_authenticated != True:
            # Зарегистрированный пользователь — считаем, что оплата прошла
            return JsonResponse({
                'success': True,
                'is_paid': True,
                'payment_status': 'Оплачено',  # Можно заменить на нужное отображение
                'order_id': None  # Можно оставить пустым или передать ID пользователя
            })

        # Для незарегистрированных пользователей
        try:
            if order_id:
                order = Order.objects.get(id=order_id)
            elif order_key:
                order = Order.objects.get(key=order_key)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Не указан ID или ключ заказа'
                })

            return JsonResponse({
                'success': True,
                'is_paid': order.is_paid(),
                'payment_status': order.get_payment_status_display(),
                'order_id': order.id
            })

        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Заказ не найден'
            })


@csrf_exempt
@require_POST
def create_order(request):
    try:
        # Получаем JSON-данные из тела запроса
        data = json.loads(request.body.decode('utf-8'))

        items = data.get('items', [])
        if not items:
            return JsonResponse({'success': False, 'message': 'Корзина пуста'})

        # Создаем заказ
        order = Order(
            # Укажите необходимые поля, например:
            status=1,  # Статус "Новый" или другой по логике
            # Можно установить дату, если нужно
            # date_created=timezone.now(),
        )

        # Связываем с пользователем, если авторизован
        if request.user.is_authenticated:
            order.user = request.user

        # Устанавливаем сумму заказа
        total_amount = 0

        # Создаем заказ и связываем с выбранными продуктами
        order.save()  # Сначала сохраняем, чтобы иметь id

        for item in items:
            try:
                product = Products.objects.get(slug=item['slug'])
                quantity = int(item['quantity'])
                amount = product.price * quantity

                selected_product = SelectedProduct.objects.create(
                    product=product,
                    quantity=quantity,
                    amount=amount,
                    status=2,  # Статус "Оплачен" или по логике
                    offline=True,
                    user=request.user if request.user.is_authenticated else None,
                    session_key=request.session.session_key if hasattr(request.session, 'session_key') else None,
                    order=order  # Связь с заказом
                )

                total_amount += amount

            except Products.DoesNotExist:
                continue
            except Exception as e:
                # Логирование ошибки
                print(f"Error processing product {item.get('slug')}: {str(e)}")
                continue

        # Обновляем сумму заказа
        order.amount = total_amount
        order.all_amount = total_amount
        order.save()

        # Очистка корзины (если используете Cart)
        session_key = request.session.session_key
        if session_key:
            carts = Cart.objects.filter(session_key=session_key)
            for cart in carts:
                cart.selectedproduct.clear()
                cart.delete()

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': 'Заказ успешно создан'
        })

    except Exception as e:
        import traceback
        print(f"Error in create_order: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': f'Ошибка: {str(e)}'})



@csrf_exempt
def ajax_get_tags(request):
    """Получить все теги для выпадающего списка"""
    try:
        tags = Tag.objects.all().values('id', 'name', 'blocked')
        return JsonResponse({
            'status': 'success',
            'tags': list(tags)
        })
    except Exception as e:
        print(e)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@csrf_exempt
def ajax_get_tags_list(request):
    """Получить все теги для списка управления"""
    try:
        tags = Tag.objects.all().values('id', 'name', 'blocked')
        return JsonResponse({
            'status': 'success',
            'tags': list(tags)
        })
    except Exception as e:
        print(e)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@csrf_exempt
@require_POST
def ajax_create_tag(request):
    """Создать новый тег"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({
                'status': 'error',
                'message': 'Название тега не может быть пустым'
            })

        # Проверяем, существует ли уже тег с таким именем
        if Tag.objects.filter(name__iexact=name).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Тег с таким названием уже существует'
            })

        tag = Tag.objects.create(name=name)

        return JsonResponse({
            'status': 'success',
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'blocked': tag.blocked
            }
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@csrf_exempt
@require_POST
def ajax_edit_tag(request):
    """Редактировать тег"""
    try:
        data = json.loads(request.body)
        tag_id = data.get('tag_id')
        name = data.get('name', '').strip()

        if not name:
            return JsonResponse({
                'status': 'error',
                'message': 'Название тега не может быть пустым'
            })

        try:
            tag = Tag.objects.get(id=tag_id)

            # Проверяем, существует ли уже тег с таким именем (кроме текущего)
            if Tag.objects.filter(name__iexact=name).exclude(id=tag_id).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Тег с таким названием уже существует'
                })

            tag.name = name
            tag.save()

            return JsonResponse({
                'status': 'success'
            })
        except Tag.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Тег не найден'
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@csrf_exempt
def ajax_toggle_tag(request):
    """Блокировать/разблокировать тег"""
    try:
        data = json.loads(request.body)
        tag_id = data.get('tag_id')
        blocked = data.get('blocked', False)

        try:
            tag = Tag.objects.get(id=tag_id)
            tag.blocked = blocked
            tag.save()

            return JsonResponse({
                'status': 'success'
            })
        except Tag.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Тег не найден'
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


class ProductExpensePositionListView(View):
    def get(self, request):
        positions = ProductExpensePosition.objects.all()
        data = [
            {
                'id': pos.id,
                'name': pos.name,
                'count': pos.count,
            }
            for pos in positions
        ]
        return JsonResponse({'status': 'success', 'positions': data})


class ProductExpensePositionDeleteView(View):
    def post(self, request, pk):
        position = get_object_or_404(ProductExpensePosition, pk=pk)
        position.delete()
        return JsonResponse({'status': 'success'})


class ProductExpensePurchaseListView(View):
    def get(self, request):
        purchases = ProductExpensePurchase.objects.all()
        data = [
            {
                'id': purchase.id,
                'productexpenseposition': purchase.productexpenseposition.id if purchase.productexpenseposition else None,
                'manufacturers': purchase.manufacturers.id if purchase.manufacturers else None,
                'count': purchase.count,
                'price': purchase.price,
                'data': purchase.data.strftime('%Y-%m-%d') if purchase.data else None,
            }
            for purchase in purchases
        ]
        return JsonResponse({'status': 'success', 'purchases': data})


@require_POST
@csrf_exempt
def ajax_update_media_positions(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        positions = data.get('positions', [])

        # Обновляем позиции медиа файлов
        for item in positions:
            media_id = item.get('media_id')
            position = item.get('position')
            try:
                media = ProductsGallery.objects.get(id=media_id)
                media.position = position
                media.save()
            except ProductsGallery.DoesNotExist:
                continue

        return JsonResponse({'status': 'success', 'message': 'Позиции обновлены'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_POST
@csrf_exempt
def update_product_positions(request):
    try:
        data = json.loads(request.body)
        positions = data.get('positions', [])
        for item in positions:
            product_id = item.get('id')
            position = item.get('position')

            try:
                print(item)
                product = Products.objects.get(id=product_id)
                print(product)
                product.position = position
                product.save()
            except Products.DoesNotExist:
                continue

        return JsonResponse({'status': 'success', 'message': 'Позиции обновлены'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


class ProductsListView(ListView):
    model = Products
    template_name = "moderations/product_list.html"
    context_object_name = "products"
    paginate_by = 50

    def get_queryset(self):
        request = self.request
        user = request.user
        get_params = request.GET
        queryset = super().get_queryset()

        # Фильтрация по типу пользователя
        if user.type in [2, 3]:
            queryset = queryset.filter(
                Q(manufacturers__owner=user) |
                Q(manufacturers__assistant=user)
            )

        # Применение фильтров из GET
        if get_params.get("type"):
            queryset = queryset.filter(type=get_params.get("type"))

        if get_params.get("typeofchoice"):
            queryset = queryset.filter(typeofchoice=get_params.get("typeofchoice"))

        if get_params.get("slug"):
            queryset = queryset.filter(slug__icontains=get_params.get("slug"))

        if get_params.get("name"):
            queryset = queryset.filter(name__icontains=get_params.get("name"))

        if get_params.get("quantity"):
            queryset = queryset.filter(quantity=get_params.get("quantity"))

        if get_params.get("review_rating"):
            queryset = queryset.filter(review_rating=get_params.get("review_rating"))

        if get_params.get("review_count"):
            queryset = queryset.filter(review_count=get_params.get("review_count"))

        if get_params.get("review_all_sum"):
            queryset = queryset.filter(review_all_sum=get_params.get("review_all_sum"))

        if get_params.get("price"):
            queryset = queryset.filter(price=get_params.get("price"))

        if get_params.get("order") in ["true", "false"]:
            queryset = queryset.filter(order=(get_params.get("order") == "true"))

        if get_params.get("search_category"):
            queryset = queryset.filter(
                category__id=get_params.get("search_category"))  # Используем category_id, если поле в модели category

        if get_params.get("stocks") in ["true", "false"]:
            queryset = queryset.filter(stocks=(get_params.get("stocks") == "true"))

        if get_params.get("manufacturers"):
            queryset = queryset.filter(manufacturers=get_params.get("manufacturers"))

        if get_params.get("valute"):
            queryset = queryset.filter(valute=get_params.get("valute"))

        if get_params.get("site"):
            queryset = queryset.filter(site=get_params.get("site"))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_params"] = self.request.GET.copy()
        context["total_products"] = self.get_queryset().count()
        context["categories"] = Categories.objects.all()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductCreateRedirectView(View):
    def get(self, request, *args, **kwargs):
        default_manufacturer = Manufacturers.objects.first()
        current_site = Site.objects.get_current()

        # Сначала создаем пустой продукт
        product = Products.objects.create()

        # Затем добавляем связи для M2M
        if default_manufacturer:
            product.manufacturers.set([default_manufacturer])
        product.site.set([current_site])

        return redirect("moderation:product_edit", pk=product.pk)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductUpdateView(UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = "moderations/product_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == 3:
            return redirect("moderation:product_variants_update", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("moderation:products")

    def form_valid(self, form):
        product = form.save(commit=False)
        print(form)
        print(self.request.POST)
        # Удаление обложки
        if self.request.POST.get("delete_cover") == "true" and product.cover:
            product.cover.delete(save=False)
            product.cover = None

        category_ids = self.request.POST.getlist('category')
        if category_ids:
            categoryes = set()


            for cat_id in category_ids:
                category = Categories.objects.get(id=int(cat_id))
                categoryes.add(category)

            product.category.set(categoryes)
            product.save()

        # Удаление превью
        if self.request.POST.get("delete_previev") == "true" and product.previev:
            product.previev.delete(save=False)
            product.previev = None

        # Удаление файлов из галереи
        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            ProductsGallery.objects.filter(
                id__in=delete_files_ids.split(","), products=product
            ).delete()

        product.save()
        form.save_m2m()

        # Добавляем новые файлы в галерею (здесь поле image)
        files = self.request.FILES.getlist("files")
        for file in files:
            ProductsGallery.objects.create(products=product, image=file)

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        optional_fields = [
            "quantity",
            "review_rating",
            "review_count",
            "review_all_sum",
            "manufacturer_identifier",
        ]
        for field_name in optional_fields:
            if field_name in form.fields:
                form.fields[field_name].required = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form is None:
            form = self.get_form()

        language_field_map = getattr(form, 'language_field_map', {})
        languages = list(language_field_map.keys())

        # Список базовых полей, которые хотим группировать по языкам
        base_fields = [
            'propertytitle',
            'description',
            'name',
            'title',
            'metadescription',
            'fragment',
            'propertydescription',
        ]

        grouped_fields = {}

        for base_field in base_fields:
            grouped_fields[base_field] = {}
            # Если есть поле без суффикса (дефолтное)
            if base_field in form.fields:
                grouped_fields[base_field]['default'] = form[base_field]
            # Добавляем языковые версии
            for lang_code in languages:
                field_name = f"{base_field}_{lang_code}"
                if field_name in form.fields:
                    grouped_fields[base_field][lang_code] = form[field_name]

        product_expenses = []
        if self.object.pk:
            product = get_object_or_404(Products, pk=self.object.pk)
            product_expenses = ProductExpense.objects.filter(product=product)

        context['current_lang'] = get_language()
        context['language_field_map'] = language_field_map
        context['grouped_fields'] = grouped_fields
        context['languages'] = languages
        context['all_expenses'] = ProductExpensePosition.objects.all()
        context['product_expenses'] = product_expenses
        context['brands'] = Brands.objects.all()
        context['manufacturers'] = Manufacturers.objects.all()
        categories = Categories.objects.all()
        category_tree = get_category_tree(categories)
        context['category_tree'] = category_tree
        print("DEBUG: grouped_fields keys:", grouped_fields.keys())

        if self.object:
            context["existing_files"] = self.object.productsgallery_set.all()
            context['all_tags'] = Tag.objects.all()
            context["stock_availability"] = StockAvailability.objects.filter(
                products=self.object
            ).select_related("storage")
            context["productsprice"] = self.object.products_prices.all()
            context["costprice"] = self.object.cost_prices.all()

            context["storages"] = Storage.objects.all()  # Все склады

        return context

    def form_invalid(self, form):
        print("Ошибки формы:")
        print(form.errors.as_text())
        return self.render_to_response(self.get_context_data(form=form))


def get_category_tree(categories, parent=None):
    tree = []
    for category in categories:
        if category.parent == parent:
            children = get_category_tree(categories, category)
            tree.append({
                'category': category,
                'children': children
            })
    return tree


class HRChangeLogListView(ListView):
    model = HRChangeLog
    context_object_name = "changelogs"
    template_name = "moderations/hr_change_log_list.html"
    paginate_by = 20

    def get_queryset(self):
        return HRChangeLog.objects.filter(user__id=self.kwargs["user_id"]).order_by("-time_change")


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:products")

    def post(self, request):
        data = json.loads(request.body)
        blogs_ids = data.get("blogs_ids", [])
        if blogs_ids:
            Products.objects.filter(id__in=blogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


def load_atributes(request):
    variable_id = request.GET.get("variable_id")
    atribs = Atribute.objects.filter(variable_id=variable_id).values("id", "name")
    return JsonResponse(list(atribs), safe=False)


def ajax_load_atributes(request):
    variable_id = request.GET.get("variable_id")
    print(f"[SERVER] Получен variable_id: {variable_id}")

    if not variable_id:
        return JsonResponse([], safe=False)

    atributes = Atribute.objects.filter(variable_id=variable_id).values("id", "name")
    result = list(atributes)

    print(f"[SERVER] Найдено атрибутов: {len(result)}")
    for attr in result:
        print(f"[SERVER] Атрибут: {attr}")

    return JsonResponse(result, safe=False)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductUpdateVariateView(UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = "moderations/product_variable_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == 1:
            return redirect("moderation:product_edit", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("moderation:products")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        optional_fields = [
            "quantity",
            "review_rating",
            "review_count",
            "review_all_sum",
            "manufacturer_identifier",
        ]
        for field in optional_fields:
            if field in form.fields:
                form.fields[field].required = False
        return form

    def get_variable_formset(self):
        return ProductsVariableFormSet(
            self.request.POST or None,
            self.request.FILES or None,
            queryset=ProductsVariable.objects.filter(products=self.object),
        )

    def form_valid(self, form):
        product = form.save(commit=False)

        # Обработка удаления обложки
        if self.request.POST.get("delete_cover") == "true" and product.cover:
            product.cover.delete(save=False)
            product.cover = None

        # Обработка удаления превью
        if self.request.POST.get("delete_previev") == "true" and product.previev:
            product.previev.delete(save=False)
            product.previev = None

        # Обработка удаления изображений из галереи
        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            ProductsGallery.objects.filter(
                id__in=delete_files_ids.split(","), products=product
            ).delete()

        product.save()
        form.save_m2m()

        # Сохраняем файлы в галерею
        for file in self.request.FILES.getlist("files"):
            ProductsGallery.objects.create(products=product, image=file)

        # Обработка формы вариаций
        variable_formset = self.get_variable_formset()
        if variable_formset.is_valid():
            instances = variable_formset.save(commit=False)
            for instance in instances:
                instance.products = product
                instance.save()
            variable_formset.save_m2m()

            # Удалённые формы
            for deleted in variable_formset.deleted_objects:
                deleted.delete()
        else:
            return self.render_to_response(
                self.get_context_data(form=form, variable_formset=variable_formset)
            )

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def form_valid(self, form):
        product = form.save(commit=False)

        category_ids = self.request.POST.getlist('category')
        if category_ids:
            categoryes = set()


            for cat_id in category_ids:
                category = Categories.objects.get(id=int(cat_id))
                categoryes.add(category)

            product.category.set(categoryes)
            product.save()


        # Удаление файлов
        if self.request.POST.get("delete_cover") == "true" and product.cover:
            product.cover.delete(save=False)
            product.cover = None

        if self.request.POST.get("delete_previev") == "true" and product.previev:
            product.previev.delete(save=False)
            product.previev = None

        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            ProductsGallery.objects.filter(
                id__in=delete_files_ids.split(","), products=product
            ).delete()

        product.save()
        form.save_m2m()

        for file in self.request.FILES.getlist("files"):
            ProductsGallery.objects.create(products=product, image=file)

        # --- Форма вариаций ---
        variable_formset = self.get_variable_formset()

        if variable_formset.is_valid():
            instances = variable_formset.save(commit=False)
            for instance in instances:
                instance.products = product
                instance.save()
            variable_formset.save_m2m()

            for deleted in variable_formset.deleted_objects:
                deleted.delete()
        else:
            # Вывод ошибок в консоль
            print("❌ Ошибки в variable_formset:")
            for i, form in enumerate(variable_formset.forms):
                if form.errors:
                    print(f"Форма #{i + 1} ошибки: {form.errors.as_text()}")

            if variable_formset.non_form_errors():
                print("Общие ошибки формы:", variable_formset.non_form_errors())

            messages.error(
                self.request,
                "Ошибки при сохранении вариаций. Проверьте заполненные поля.",
            )
            return self.render_to_response(
                self.get_context_data(form=form, variable_formset=variable_formset)
            )

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        form = context.get('form')
        if form is None:
            form = self.get_form()

        language_field_map = getattr(form, 'language_field_map', {})
        languages = list(language_field_map.keys())

        # Список базовых полей, которые хотим группировать по языкам
        base_fields = [
            'propertytitle',
            'description',
            'name',
            'title',
            'metadescription',
            'fragment',
            'propertydescription',
        ]

        grouped_fields = {}

        for base_field in base_fields:
            grouped_fields[base_field] = {}
            # Если есть поле без суффикса (дефолтное)
            if base_field in form.fields:
                grouped_fields[base_field]['default'] = form[base_field]
            # Добавляем языковые версии
            for lang_code in languages:
                field_name = f"{base_field}_{lang_code}"
                if field_name in form.fields:
                    grouped_fields[base_field][lang_code] = form[field_name]

        product_expenses = []
        if self.object.pk:
            product = get_object_or_404(Products, pk=self.object.pk)
            product_expenses = ProductExpense.objects.filter(product=product)

        context['current_lang'] = get_language()
        context['language_field_map'] = language_field_map
        context['grouped_fields'] = grouped_fields
        context['languages'] = languages
        context['all_expenses'] = ProductExpensePosition.objects.all()
        context['product_expenses'] = product_expenses
        context['brands'] = Brands.objects.all()
        context['manufacturers'] = Manufacturers.objects.all()
        categories = Categories.objects.all()
        category_tree = get_category_tree(categories)
        context['category_tree'] = category_tree

        print("DEBUG: grouped_fields keys:", grouped_fields.keys())
        context['all_tags'] = Tag.objects.all()
        context["existing_files"] = product.productsgallery_set.all()
        context["stock_availability"] = StockAvailability.objects.filter(
            products=product
        ).select_related("storage")
        context["productsprice"] = product.products_prices.all()
        context["costprice"] = product.cost_prices.all()
        context["productvariables"] = ProductsVariable.objects.filter(
            products=product
        ).prefetch_related("attribute")

        if "variable_formset" not in kwargs:
            variable_formset = self.get_variable_formset()
            context["variable_formset"] = variable_formset
        else:
            context["variable_formset"] = kwargs["variable_formset"]

        # Для добавления через JS
        context["empty_form"] = ProductsVariableFormSet(
            queryset=ProductsVariable.objects.none()
        ).empty_form
        context["storages"] = Storage.objects.all()

        return context


@csrf_exempt
@login_required
def create_product_variants(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=400)

    try:
        product = Products.objects.get(pk=pk)
        data = json.loads(request.body)
        variants = data.get("variants", [])

        for var in variants:
            variant = ProductsVariable.objects.create(
                products=product,
                name=var["name"],
                price=var["price"],
                quantity=var["quantity"],
                defaultposition=var.get("defaultposition", False),
            )
            variant.attribute.set(var["attribute_ids"])

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class CreateStockAvailabilityView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8"))
            product_id = data.get("product_id")
            stocks = data.get("stocks")

            print("Полученные данные:", data)

            if not product_id or not isinstance(stocks, list):
                return JsonResponse(
                    {"status": "error", "message": "Некорректные данные"}, status=400
                )

            product = get_object_or_404(Products, id=product_id)

            created_or_updated = []

            for stock in stocks:
                storage_id = stock.get("storage_id")
                quantity = stock.get("quantity")

                print("Обработка:", storage_id, quantity)

                if not storage_id or quantity is None:
                    continue

                storage = get_object_or_404(Storage, id=storage_id)

                obj, created = StockAvailability.objects.update_or_create(
                    products=product, storage=storage, defaults={"quantity": quantity}
                )

                created_or_updated.append(
                    {"storage_id": storage.id, "quantity": obj.quantity}
                )

            return JsonResponse({"status": "success", "stocks": created_or_updated})

        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqsProductsList(ListView):
    template_name = "moderations/faqs_list.html"
    model = FaqsProducts
    context_object_name = "faqs_list"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # 🔐 Ограничение доступа: только владельцы и ассистенты
        if user.type in [2, 3]:
            queryset = queryset.filter(
                Q(product__manufacturers__owner=user) |
                Q(product__manufacturers__assistant=user)
            )

        return queryset.order_by("-create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = self.get_queryset()

        # 🔍 Поиск по ID
        search_id = self.request.GET.get("search_id", "")
        if search_id:
            queryset = queryset.filter(pk=search_id)

        # 🔍 Поиск по вопросу
        search_name = self.request.GET.get("search_name", "")
        if search_name:
            queryset = queryset.filter(question__icontains=search_name)

        # 🔍 Поиск по дате
        search_date = self.request.GET.get("search_date", "")
        if search_date:
            try:
                search_date_obj = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                queryset = queryset.filter(create__date=search_date_obj)
            except ValueError:
                pass

        # 📄 Пагинация
        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        context["filter_params"] = self.request.GET.copy()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqsProductsCreateView(LoginRequiredMixin, CreateView):
    model = FaqsProducts
    fields = "__all__"
    template_name = "moderations/faqsproducts_form.html"
    success_url = reverse_lazy("moderation:faq_product")
    context_object_name = "faqs"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqsProductsUpdateView(LoginRequiredMixin, UpdateView):
    model = FaqsProducts
    fields = "__all__"
    template_name = "moderations/faqsproducts_form.html"
    success_url = reverse_lazy("moderation:faq_product")
    context_object_name = "faqs"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class FaqsProductsDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:faq_product")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            FaqsProducts.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductCommentList(ListView):
    template_name = "moderations/productcomments_list.html"
    model = ProductComment
    context_object_name = "productcomments"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        try:
            user_type = int(user.type)
        except Exception:
            user_type = -1  # или любое невалидное значение

        if user_type in [2, 3]:
            queryset = queryset.filter(
                Q(ticket__product__manufacturers__owner=user) |
                Q(ticket__product__manufacturers__assistant=user)
            )
        return queryset.order_by("-create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            queryset = queryset.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            queryset = queryset.filter(content__icontains=search_name)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            try:
                date_obj = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                queryset = queryset.filter(create__date=date_obj)
            except ValueError:
                pass

        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get("page")
        try:
            comment_list = paginator.page(page)
        except PageNotAnInteger:
            comment_list = paginator.page(1)
        except EmptyPage:
            comment_list = paginator.page(paginator.num_pages)

        context["faq_list"] = comment_list
        context["paginator"] = paginator
        context["page_obj"] = comment_list
        context["filter_params"] = self.request.GET.copy()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductCommentCreateView(LoginRequiredMixin, CreateView):
    model = ProductComment
    fields = "__all__"
    template_name = "moderations/productcomments_form.html"
    success_url = reverse_lazy("moderation:productcomments")
    context_object_name = "productcomments"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductCommentUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductComment
    fields = "__all__"
    template_name = "moderations/productcomments_form.html"
    success_url = reverse_lazy("moderation:productcomments")
    context_object_name = "productcomments"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ProductCommentDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:productcomments")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            ProductComment.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# Валюта
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ValuteList(LoginRequiredMixin, ListView):
    template_name = "moderations/valute_list.html"
    model = Valute
    context_object_name = "valute"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faq = Valute.objects.order_by("-create").all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            faq = faq.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            faq = faq.filter(question__icontains=search_name)

        search_date = self.request.GET.get("search_date", "")
        if search_date:
            # Преобразуем строку даты в объект datetime
            try:
                search_date = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                faq = faq.filter(create__date=search_date)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(faq, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ValuteCreateView(LoginRequiredMixin, CreateView):
    model = Valute
    fields = "__all__"
    template_name = "moderations/valute_form.html"
    success_url = reverse_lazy("moderation:valute")
    context_object_name = "valute"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ValuteUpdateView(LoginRequiredMixin, UpdateView):
    model = Valute
    fields = "__all__"
    template_name = "moderations/valute_form.html"
    success_url = reverse_lazy("moderation:valute")
    context_object_name = "valute"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ValuteDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:valute")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            Valute.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# ЗАявки
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ApplicationsProductsList(LoginRequiredMixin, ListView):
    template_name = "moderations/applicationsproducts_list.html"
    model = ApplicationsProducts
    context_object_name = "applicationsproducts"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = ApplicationsProducts.objects.all()

        # 🔐 Фильтрация по владельцу или ассистенту производителя
        if user.type in [2, 3]:
            queryset = queryset.filter(
                Q(products__manufacturers__owner=user) |
                Q(products__manufacturers__assistant=user)
            )

        return queryset.order_by("-create")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        # Поиск по ID
        search_id = self.request.GET.get("search_id", "")
        if search_id:
            queryset = queryset.filter(pk=search_id)

        # Поиск по дате создания
        search_date = self.request.GET.get("search_date", "")
        if search_date:
            try:
                date_obj = timezone.datetime.strptime(search_date, "%Y-%m-%d").date()
                queryset = queryset.filter(create__date=date_obj)
            except ValueError:
                pass

        # Пагинация
        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        context["filter_params"] = self.request.GET.copy()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ApplicationsProductsCreateView(LoginRequiredMixin, CreateView):
    model = ApplicationsProducts
    fields = "__all__"
    template_name = "moderations/applicationsproducts_form.html"
    success_url = reverse_lazy("moderation:applicationsproducts")
    context_object_name = "applicationsproducts"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ApplicationsProductsUpdateView(LoginRequiredMixin, UpdateView):
    model = ApplicationsProducts
    fields = "__all__"
    template_name = "moderations/applicationsproducts_form.html"
    success_url = reverse_lazy("moderation:applicationsproducts")
    context_object_name = "applicationsproducts"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ApplicationsProductsDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:applicationsproducts")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            ApplicationsProducts.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# Вариация
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VariableList(LoginRequiredMixin, ListView):
    template_name = "moderations/variable_list.html"
    model = Variable
    context_object_name = "variable"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faq = Variable.objects.all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            faq = faq.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            faq = faq.filter(question__icontains=search_name)

        # Пагинация
        paginator = Paginator(faq, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VariableCreateView(LoginRequiredMixin, CreateView):
    model = Variable
    fields = "__all__"
    template_name = "moderations/variable_form.html"
    success_url = reverse_lazy("moderation:variable")
    context_object_name = "variable"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VariableUpdateView(LoginRequiredMixin, UpdateView):
    model = Variable
    fields = "__all__"
    template_name = "moderations/variable_form.html"
    success_url = reverse_lazy("moderation:variable")
    context_object_name = "variable"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


def load_attributes(request, variable_id):
    attributes = Atribute.objects.filter(variable_id=variable_id)
    html = render_to_string(
        "moderations/atributes_list.html", {"attributes": attributes}
    )
    return JsonResponse({"html": html})


@require_POST
@csrf_exempt
def save_atribute(request, variable_id, atribute_id=None):
    variable = get_object_or_404(Variable, id=variable_id)
    instance = Atribute.objects.filter(id=atribute_id).first() if atribute_id else None

    form = AtributeForm(request.POST, request.FILES, instance=instance)
    if form.is_valid():
        atribute = form.save(commit=False)
        atribute.variable = variable
        atribute.save()
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"success": False, "errors": form.errors})


@require_POST
@csrf_exempt
def delete_atribute(request, atribute_id):
    try:
        Atribute.objects.get(id=atribute_id).delete()
        return JsonResponse({"success": True})
    except Atribute.DoesNotExist:
        return HttpResponseBadRequest("Atribute not found")


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VariableDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:variable")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            Variable.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# Склады
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class StorageList(LoginRequiredMixin, ListView):
    template_name = "moderations/storages_list.html"
    model = Storage
    context_object_name = "storages"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faq = Storage.objects.all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            faq = faq.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            faq = faq.filter(question__icontains=search_name)

        # Пагинация
        paginator = Paginator(faq, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class StorageCreateView(LoginRequiredMixin, CreateView):
    model = Storage
    fields = "__all__"
    template_name = "moderations/storages_form.html"
    success_url = reverse_lazy("moderation:storages")
    context_object_name = "storages"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class StorageUpdateView(LoginRequiredMixin, UpdateView):
    model = Storage
    fields = "__all__"
    template_name = "moderations/storages_form.html"
    success_url = reverse_lazy("moderation:storages")
    context_object_name = "storages"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class StorageDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:storages")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            Storage.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


# Магазины
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ManufacturersList(LoginRequiredMixin, ListView):
    template_name = "moderations/manufacturers_list.html"
    model = Manufacturers
    context_object_name = "manufacturers"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faq = Manufacturers.objects.all()

        search_id = self.request.GET.get("search_id", "")
        if search_id:
            faq = faq.filter(pk=search_id)

        search_name = self.request.GET.get("search_name", "")
        if search_name:
            faq = faq.filter(question__icontains=search_name)

        # Пагинация
        paginator = Paginator(faq, 10)  # 20 элементов на страницу
        page = self.request.GET.get("page")
        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list  # Передаем отфильтрованные задачи
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


class MyManufacturerListView(LoginRequiredMixin, ListView):
    model = Manufacturers
    template_name = "moderations/mymanufacturers_list.html"
    context_object_name = "manufacturers"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Manufacturers.objects.filter(
            Q(owner=user) | Q(assistant=user)
        ).distinct()

        # Фильтрация по ID
        search_id = self.request.GET.get("search_id")
        if search_id:
            queryset = queryset.filter(pk=search_id)

        # Фильтрация по имени (если нужно по названию)
        search_name = self.request.GET.get("search_name")
        if search_name:
            queryset = queryset.filter(name__icontains=search_name)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Переопределим вручную пагинацию, если нужно отдельно
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page = self.request.GET.get("page")

        try:
            faq_list = paginator.page(page)
        except PageNotAnInteger:
            faq_list = paginator.page(1)
        except EmptyPage:
            faq_list = paginator.page(paginator.num_pages)

        context["faq_list"] = faq_list
        context["paginator"] = paginator
        context["page_obj"] = faq_list
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ManufacturersDashboardView(DetailView):
    template_name = "moderations/manufacturers_dashbord.html"
    context_object_name = "manufacturers"
    model = Manufacturers
    pk_url_kwarg = 'id'


from shop.serializers import ProductExpensePurchaseSerializer, ManufacturersExpenseSerializer, \
    SelectedProductSerializer, WithdrawalSerializer, ManufacturersIncomeSerializer, AggregatedExpenseSerializer
from collections import defaultdict
from django.db.models import Count
from rest_framework.exceptions import NotFound


class AggregatedExpenseDailyView(APIView):
    def get(self, request, *args, **kwargs):
        # Получаем фильтры из запроса
        store = request.query_params.get('store', None)
        data = request.query_params.get('data', None)

        # Формируем фильтрацию
        filters = {}

        if store:
            try:
                store = int(store)  # Предполагаем, что store передается как ID
                filters['store_id'] = store
            except ValueError:
                return Response({"detail": "Invalid store ID"}, status=status.HTTP_400_BAD_REQUEST)

        if data:
            try:
                data = datetime.strptime(data, '%Y-%m-%d')  # Пример формата '2025-08-24'
                filters['data'] = data
            except ValueError:
                return Response({"detail": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем данные с фильтрацией
        expenses = AggregatedExpense.objects.filter(**filters)

        # Если нет данных по фильтрам, возвращаем пустой список
        if not expenses:
            return Response([], status=status.HTTP_200_OK)

        # Выводим данные
        data_output = []
        for expense in expenses:
            data_output.append({
                "ID": expense.id,
                "Store": expense.store.name,
                "Date": expense.data,
                "Revenue": expense.revenue_by_products,
                "Expenses by products": expense.expenses_by_products,
                "Expenses by store": expense.expenses_by_store,
                "Expenses by employee": expense.expenses_by_employee,
                "Income": expense.income,
            })

        return Response(data_output, status=status.HTTP_200_OK)





class ExpenseListView(APIView):
    def get(self, request, *args, **kwargs):
        # Получение параметров из запроса
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        manufacturer_id = request.query_params.get('manufacturer_id')


        # Фильтрация для ProductExpensePurchase
        queryset_product_expense = ProductExpensePurchase.objects.all()
        if date_from:
            queryset_product_expense = queryset_product_expense.filter(data__gte=date_from)
        if date_to:
            queryset_product_expense = queryset_product_expense.filter(data__lte=date_to)
        if manufacturer_id:
            queryset_product_expense = queryset_product_expense.filter(manufacturers_id=manufacturer_id)

        # Фильтрация для ManufacturersExpense
        queryset_manufacturer_expense = ManufacturersExpense.objects.all()
        if date_from:
            queryset_manufacturer_expense = queryset_manufacturer_expense.filter(data__gte=date_from)
        if date_to:
            queryset_manufacturer_expense = queryset_manufacturer_expense.filter(data__lte=date_to)
        if manufacturer_id:
            queryset_manufacturer_expense = queryset_manufacturer_expense.filter(manufacturers_id=manufacturer_id)

        # Фильтрация для SelectedProduct с условием status=2 и с фильтрацией через продукт
        queryset_selected_products = SelectedProduct.objects.all()
        if manufacturer_id:
            queryset_selected_products = queryset_selected_products.filter(product__manufacturers__id=manufacturer_id)
        queryset_selected_products = queryset_selected_products.filter(status=2)

        # Фильтрация для Withdrawal
        queryset_withdrawals = Withdrawal.objects.all()
        if date_from:
            queryset_withdrawals = queryset_withdrawals.filter(create__gte=date_from)
        if date_to:
            queryset_withdrawals = queryset_withdrawals.filter(create__lte=date_to)
        if manufacturer_id:
            queryset_withdrawals = queryset_withdrawals.filter(manufacturers_id=manufacturer_id)

        # Фильтрация для ManufacturersIncome
        queryset_manufacturers_income = ManufacturersIncome.objects.all()
        if date_from:
            queryset_manufacturers_income = queryset_manufacturers_income.filter(data__gte=date_from)
        if date_to:
            queryset_manufacturers_income = queryset_manufacturers_income.filter(data__lte=date_to)
        if manufacturer_id:
            queryset_manufacturers_income = queryset_manufacturers_income.filter(manufacturers_id=manufacturer_id)

        # Сериализация данных
        product_expense_serializer = ProductExpensePurchaseSerializer(queryset_product_expense, many=True)
        manufacturer_expense_serializer = ManufacturersExpenseSerializer(queryset_manufacturer_expense, many=True)
        selected_product_serializer = SelectedProductSerializer(queryset_selected_products, many=True)
        withdrawal_serializer = WithdrawalSerializer(queryset_withdrawals, many=True)
        manufacturers_income_serializer = ManufacturersIncomeSerializer(queryset_manufacturers_income, many=True)

        # Объединение результатов
        data = {
            "product_expenses": product_expense_serializer.data,
            "manufacturer_expenses": manufacturer_expense_serializer.data,
            "selected_products": selected_product_serializer.data,
            "withdrawals": withdrawal_serializer.data,  # Добавление данных по выводу средств
            "manufacturers_incomes": manufacturers_income_serializer.data  # Добавление данных по доходам производителей
        }


        return Response(data, status=status.HTTP_200_OK)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ManufacturersCreateView(LoginRequiredMixin, CreateView):
    model = Manufacturers
    fields = "__all__"
    template_name = "moderations/manufacturers_form.html"
    success_url = reverse_lazy("moderation:manufacturers")
    context_object_name = "manufacturers"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form is None:
            form = self.get_form()

        language_field_map = getattr(form, 'language_field_map', {})
        languages = list(language_field_map.keys())

        # Список базовых полей, которые хотим группировать по языкам
        base_fields = [
            'propertytitle',
            'description',
            'name',
            'title',
            'metadescription',
            'fragment',
            'propertydescription',
        ]

        grouped_fields = {}

        for base_field in base_fields:
            grouped_fields[base_field] = {}
            # Если есть поле без суффикса (дефолтное)
            if base_field in form.fields:
                grouped_fields[base_field]['default'] = form[base_field]
            # Добавляем языковые версии
            for lang_code in languages:
                field_name = f"{base_field}_{lang_code}"
                if field_name in form.fields:
                    grouped_fields[base_field][lang_code] = form[field_name]

        context['current_lang'] = get_language()
        context['language_field_map'] = language_field_map
        context['grouped_fields'] = grouped_fields
        context['languages'] = languages

        print("DEBUG: grouped_fields keys:", grouped_fields.keys())

        if self.object:
            context["existing_files"] = self.object.productsgallery_set.all()
            context["existing_files"] = self.object.productsgallery_set.all()
            context["stock_availability"] = StockAvailability.objects.filter(
                products=self.object
            ).select_related("storage")
            context["productsprice"] = self.object.products_prices.all()
            context["costprice"] = self.object.cost_prices.all()

            context["storages"] = Storage.objects.all()  # Все склады

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ManufacturersUpdateView(LoginRequiredMixin, UpdateView):
    model = Manufacturers
    fields = "__all__"
    template_name = "moderations/manufacturers_form.html"
    success_url = reverse_lazy("moderation:manufacturers")
    context_object_name = "manufacturers"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manufacturer = self.object

        # Генерация shop_id если его нет
        if not manufacturer.shop_id:
            manufacturer.shop_id = get_random_string(12, 'abcdefghijklmnopqrstuvwxyz0123456789')
            manufacturer.save()

        # Генерация token если его нет
        if not manufacturer.token:
            manufacturer.token = get_random_string(32, 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            manufacturer.save()

        return context

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ManufacturersDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:manufacturers")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            Manufacturers.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


class ProductImportView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            # Получаем данные из запроса
            shop_id = request.data.get('shop_id')
            token = request.data.get('token')
            xml_data = request.data.get('xml_data')

            # Проверяем обязательные поля
            if not all([shop_id, token, xml_data]):
                return Response(
                    {"error": "Необходимы shop_id, token и xml_data"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверяем токен
            try:
                manufacturer = Manufacturers.objects.get(shop_id=shop_id)
                if manufacturer.token != token:
                    return Response(
                        {"error": "Неверный токен"},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
            except Manufacturers.DoesNotExist:
                return Response(
                    {"error": "Производитель не найден"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Парсим XML
            try:
                root = ET.fromstring(xml_data)
            except ET.ParseError as e:
                return Response(
                    {"error": f"Ошибка парсинга XML: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Проверяем shop_id в XML
            xml_shop_id = root.attrib.get('shop_id')
            if xml_shop_id != shop_id:
                return Response(
                    {"error": f"shop_id в XML ({xml_shop_id}) не совпадает с переданным ({shop_id})"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Обрабатываем товары в транзакции
            with transaction.atomic():
                for product_elem in root.findall('product'):
                    self.process_product(product_elem, manufacturer)

            return Response(
                {"status": "success", "message": "Товары успешно обработаны"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Ошибка обработки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def process_product(self, product_elem, manufacturer):
        # Обработка валюты
        valute_key = product_elem.find('valute').text.strip().upper()
        try:
            valute = Valute.objects.get(key__iexact=valute_key)
        except Valute.DoesNotExist:
            valute = Valute.objects.filter(default=True).first()

        # Основные данные товара
        product_data = {
            'id': product_elem.find('id').text,
            'manufacturers': manufacturer,  # Исправлено с 'manufacturer' на 'manufacturers'
            'name': product_elem.find('name').text,
            'slug': product_elem.find('slug').text,
            'price': float(product_elem.find('price').text),
            'costprice': float(product_elem.find('costprice').text),
            'quantity': int(product_elem.find('quantity').text),
            'review_rating': float(product_elem.find('review_rating').text),
            'review_count': int(product_elem.find('review_count').text),
            'review_all_sum': int(product_elem.find('review_all_sum').text),
            'description': product_elem.find('description').text if product_elem.find(
                'description') is not None else '',
            'fragment': product_elem.find('fragment').text if product_elem.find('fragment') is not None else '',
            'type': int(product_elem.find('type').text),
            'typeofchoice': int(product_elem.find('typeofchoice').text),
            'weight': float(product_elem.find('weight').text),
            'width': float(product_elem.find('width').text),
            'height': float(product_elem.find('height').text),
            'length': float(product_elem.find('length').text),
            'image': product_elem.find('image').text,
            'valute': valute,
        }

        # Создаем или обновляем товар
        product, created = Products.objects.update_or_create(
            id=product_data['id'],
            defaults=product_data
        )

        # Остальные методы обработки (категории, галерея и т.д.)
        self.process_categories(product, product_elem)
        self.process_gallery(product, product_elem)
        self.process_stocks(product, product_elem)
        self.process_variants(product, product_elem)

    def process_categories(self, product, product_elem):
        # Получаем все категории из XML
        category_names = []
        for cat_elem in product_elem.findall('.//categories/category'):
            category_name = cat_elem.text.strip()
            if category_name:
                category_names.append(category_name)

        # Получаем или создаем объекты категорий
        categories = []
        for name in category_names:
            category, _ = Categories.objects.get_or_create(name=name)
            categories.append(category)

        # Обновляем связи ManyToMany
        product.category.set(categories)

    def process_gallery(self, product, product_elem):
        # Удаляем старые изображения
        ProductsGallery.objects.filter(products=product).delete()

        # Добавляем новые изображения
        for img_elem in product_elem.findall('.//gallery/image/url'):
            image_url = img_elem.text.strip()
            if image_url:
                ProductsGallery.objects.create(
                    products=product,
                    image=image_url  # Для FileField нужно передать файл, а не URL
                )

    def process_stocks(self, product, product_elem):
        # Удаляем старые данные о складах
        StockAvailability.objects.filter(products=product).delete()

        # Добавляем новые данные о складах
        for stock_elem in product_elem.findall('.//stocks/stock'):
            storage_name = stock_elem.find('storage').text
            city = stock_elem.find('city').text
            address = stock_elem.find('address').text

            # Получаем или создаем склад
            storage, _ = Storage.objects.get_or_create(
                name=storage_name,
                defaults={
                    'city': city,
                    'address': address
                }
            )

            StockAvailability.objects.create(
                products=product,
                storage=storage,
                quantity=int(stock_elem.find('quantity').text)
            )

    def process_variants(self, product, product_elem):
        # Удаляем старые варианты
        ProductsVariable.objects.filter(products=product).delete()

        # Обрабатываем варианты из XML
        for var_elem in product_elem.findall('.//variables/variable'):
            # Создаем вариант продукта
            variant = ProductsVariable.objects.create(
                products=product,
                name=var_elem.find('name').text,
                price=product.price,  # Используем цену из основного продукта
                costprice=product.costprice,
                valute=product.valute,
                quantity=product.quantity
            )

            # Обрабатываем атрибуты варианта
            for attr_elem in var_elem.findall('.//attributes/attribute'):
                attr_name = attr_elem.text.strip()
                if attr_name:
                    attribute, _ = Atribute.objects.get_or_create(name=attr_name)
                    variant.attribute.add(attribute)


class ProductsXMLExportView(View):
    def get(self, request, xml_link):
        try:
            manufacturer = Manufacturers.objects.get(xml_link=xml_link)
        except Manufacturers.DoesNotExist:
            raise Http404("Производитель с таким xml_link не найден")

        root = ET.Element('manufacturer')
        root.set('name', manufacturer.name or '')
        root.set('shop_id', manufacturer.shop_id or '')

        products = Products.objects.filter(manufacturers=manufacturer)

        for product in products:
            product_el = ET.SubElement(root, 'product')
            ET.SubElement(product_el, 'id').text = str(product.id)
            ET.SubElement(product_el, 'name').text = product.name or ''
            ET.SubElement(product_el, 'slug').text = product.slug or ''
            ET.SubElement(product_el, 'price').text = str(product.price)
            ET.SubElement(product_el, 'costprice').text = str(product.costprice)
            ET.SubElement(product_el, 'quantity').text = str(product.quantity)
            ET.SubElement(product_el, 'review_rating').text = str(product.review_rating)
            ET.SubElement(product_el, 'review_count').text = str(product.review_count)
            ET.SubElement(product_el, 'review_all_sum').text = str(product.review_all_sum)
            ET.SubElement(product_el, 'description').text = product.description or ''
            ET.SubElement(product_el, 'fragment').text = product.fragment or ''
            ET.SubElement(product_el, 'type').text = str(product.type)
            ET.SubElement(product_el, 'typeofchoice').text = str(product.typeofchoice)
            ET.SubElement(product_el, 'weight').text = str(product.weight or 0)
            ET.SubElement(product_el, 'width').text = str(product.width or 0)
            ET.SubElement(product_el, 'height').text = str(product.height or 0)
            ET.SubElement(product_el, 'length').text = str(product.length or 0)
            ET.SubElement(product_el, 'image').text = request.build_absolute_uri(
                product.image.url) if product.image else ''
            ET.SubElement(product_el, 'valute').text = product.valute.name if product.valute else ''

            categories_el = ET.SubElement(product_el, 'categories')
            for cat in product.category.all():
                ET.SubElement(categories_el, 'category').text = cat.name

            gallery_el = ET.SubElement(product_el, 'gallery')
            for img in ProductsGallery.objects.filter(products=product):
                img_el = ET.SubElement(gallery_el, 'image')
                ET.SubElement(img_el, 'url').text = request.build_absolute_uri(img.image.url) if img.image else ''
                ET.SubElement(img_el, 'hash').text = img.image_hash or ''

            stock_el = ET.SubElement(product_el, 'stocks')
            for stock in StockAvailability.objects.filter(products=product):
                s = ET.SubElement(stock_el, 'stock')
                ET.SubElement(s, 'quantity').text = str(stock.quantity)
                ET.SubElement(s, 'storage').text = stock.storage.name
                ET.SubElement(s, 'city').text = stock.storage.city
                ET.SubElement(s, 'address').text = stock.storage.address

            variables_el = ET.SubElement(product_el, 'variables')
            for variable in Variable.objects.all():
                attributes = product.atribute.filter(variable=variable)
                if attributes.exists():
                    var_el = ET.SubElement(variables_el, 'variable')
                    ET.SubElement(var_el, 'name').text = variable.name
                    attrs_el = ET.SubElement(var_el, 'attributes')
                    for attr in attributes:
                        ET.SubElement(attrs_el, 'attribute').text = attr.name

            product_variables_el = ET.SubElement(product_el, 'product_variants')
            for var in ProductsVariable.objects.filter(products=product):
                var_el = ET.SubElement(product_variables_el, 'variant')
                ET.SubElement(var_el, 'id').text = str(var.id)
                ET.SubElement(var_el, 'name').text = var.name or ''
                ET.SubElement(var_el, 'slug').text = var.slug or ''
                ET.SubElement(var_el, 'price').text = str(var.price)
                ET.SubElement(var_el, 'costprice').text = str(var.costprice)
                ET.SubElement(var_el, 'quantity').text = str(var.quantity)
                ET.SubElement(var_el, 'image').text = request.build_absolute_uri(var.image.url) if var.image else ''
                ET.SubElement(var_el, 'weight').text = str(var.weight or 0)
                ET.SubElement(var_el, 'width').text = str(var.width or 0)
                ET.SubElement(var_el, 'height').text = str(var.height or 0)
                ET.SubElement(var_el, 'length').text = str(var.length or 0)

                attr_el = ET.SubElement(var_el, 'attributes')
                for attr in var.attribute.all():
                    ET.SubElement(attr_el, 'attribute').text = attr.name

        xml_bytes = ET.tostring(root, encoding='utf-8')
        pretty_xml = xml.dom.minidom.parseString(xml_bytes).toprettyxml(indent="  ")

        return HttpResponse(pretty_xml, content_type="application/xml")


class ProductsXLSXExportView(View):
    def get(self, request, xml_link):
        try:
            manufacturer = Manufacturers.objects.get(xml_link=xml_link)
        except Manufacturers.DoesNotExist:
            raise Http404("Производитель с таким xml_link не найден")

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        headers = [
            'ID', 'Название', 'Слаг', 'Цена', 'Себестоимость', 'Количество',
            'Тип', 'Тип выбора', 'Валюта', 'Атрибуты', 'Категории',
            'Изображения', 'Склады'
        ]
        worksheet.write_row(0, 0, headers)

        products = Products.objects.filter(manufacturers=manufacturer)
        row = 1
        for product in products:
            attributes = ", ".join([a.name for a in product.atribute.all()])
            categories = ", ".join([c.name for c in product.category.all()])
            images = ", ".join(
                [request.build_absolute_uri(i.image.url) for i in ProductsGallery.objects.filter(products=product) if
                 i.image])
            stocks = ", ".join([
                f"{s.storage.name} ({s.quantity})" for s in StockAvailability.objects.filter(products=product)
            ])

            worksheet.write_row(row, 0, [
                str(product.id), product.name, product.slug, str(product.price), str(product.costprice),
                str(product.quantity), str(product.type), str(product.typeofchoice),
                product.valute.name if product.valute else '',
                attributes, categories, images, stocks
            ])
            row += 1

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=products_export.xlsx'
        return response


class ProductsCSVExportView(View):
    def get(self, request, xml_link):
        try:
            manufacturer = Manufacturers.objects.get(xml_link=xml_link)
        except Manufacturers.DoesNotExist:
            raise Http404("Производитель с таким xml_link не найден")

        output = io.StringIO()
        writer = csv.writer(output)

        headers = [
            'ID', 'Название', 'Слаг', 'Цена', 'Себестоимость', 'Количество',
            'Тип', 'Тип выбора', 'Валюта', 'Атрибуты', 'Категории',
            'Изображения', 'Склады'
        ]
        writer.writerow(headers)

        products = Products.objects.filter(manufacturers=manufacturer)
        for product in products:
            attributes = ", ".join([a.name for a in product.atribute.all()])
            categories = ", ".join([c.name for c in product.category.all()])
            images = ", ".join(
                [request.build_absolute_uri(i.image.url) for i in ProductsGallery.objects.filter(products=product) if
                 i.image])
            stocks = ", ".join([
                f"{s.storage.name} ({s.quantity})" for s in StockAvailability.objects.filter(products=product)
            ])

            writer.writerow([
                str(product.id), product.name, product.slug, str(product.price), str(product.costprice),
                str(product.quantity), str(product.type), str(product.typeofchoice),
                product.valute.name if product.valute else '',
                attributes, categories, images, stocks
            ])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=products_export.csv'
        return response


class ImportHistoryCreateView(View):
    def get(self, request):
        form = ImportHistoryForm()
        return render(request, 'moderations/import_history_form.html', {'form': form})

    def post(self, request):
        form = ImportHistoryForm(request.POST, request.FILES)
        if form.is_valid():
            import_history = form.save(commit=False)
            import_history.user = request.user
            import_history.status = 'pending'
            import_history.created_at = timezone.now()

            # Если пользователь загрузил файл с диска
            if request.FILES.get('file'):
                import_history.file = request.FILES['file']
            else:
                # Если скачанный файл передан именем
                downloaded_filename = request.POST.get('downloaded_file_name')
                if downloaded_filename:
                    file_path = os.path.join(settings.MEDIA_ROOT, 'imports', downloaded_filename)
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            django_file = File(f)
                            # Назначаем файл в поле модели
                            import_history.file.save(downloaded_filename, django_file, save=False)

            if form.cleaned_data['file_url']:
                import_history.file_url = form.cleaned_data['file_url']

            import_history.save()
            messages.success(request, "Файл был успешно загружен и добавлен в очередь для импорта!")
            return redirect('moderation:import_history_list')

        messages.error(request, "Ошибка при загрузке файла или указании расписания.")
        return render(request, 'moderations/import_history_form.html', {'form': form})


class ImportHistoryListView(ListView):
    model = ImportHistory
    template_name = 'moderations/import_history_list.html'
    context_object_name = 'import_histories'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        # Получаем shop_id для всех Manufacturers, где user - owner или assistant
        manufacturers = Manufacturers.objects.filter(
            Q(owner=user) | Q(assistant=user)
        ).values_list('shop_id', flat=True)

        # Фильтруем ImportHistory по shop_id из списка manufacturers
        return ImportHistory.objects.filter(
            shop_id__in=manufacturers
        ).order_by('-created_at')


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SettingsModerationEditView(UpdateView):
    model = SettingsModeration
    form_class = SettingsModerationForm
    template_name = 'moderations/edit_settings.html'  # Укажите ваш шаблон
    success_url = reverse_lazy('moderation:settings_edit')  # Или другой URL для редиректа после успешного сохранения

    def get_object(self, queryset=None):
        # Получаем единственный объект или создаем новый, если его нет
        obj, created = SettingsModeration.objects.get_or_create(pk=1)
        return obj


@csrf_exempt
def import_download_file(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        if not url:
            return JsonResponse({'success': False, 'error': 'URL не передан'})

        try:
            r = requests.get(url)
            r.raise_for_status()
            ext = os.path.splitext(url)[1] or '.tmp'
            filename = f'downloaded_{uuid.uuid4().hex}{ext}'

            # Сохраняем файл в нужную папку
            path = os.path.join(settings.MEDIA_ROOT, 'imports', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, 'wb') as f:
                f.write(r.content)

            # Можно, например, создать объект ImportHistory или просто вернуть имя файла
            # Чтобы пользователь мог отправить форму с info о загруженном файле

            return JsonResponse({'success': True, 'filename': filename})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Неподдерживаемый метод'})


class LessonListView(ListView):
    model = Lesson
    template_name = "moderations/lesson/lesson_list.html"
    context_object_name = "lessons"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Lesson.objects.all()

        # Поиск по названию
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)  # фильтрация по полю name

        if not user.is_authenticated:
            queryset = queryset.filter(publishet=True)

        # Найдём всех производителей, где пользователь участвует
        manufacturers_qs = Manufacturers.objects.filter(
            Q(owner=user) | Q(assistant=user)
        )

        queryset = queryset.filter(
            Q(publishet=True) |
            Q(owner=user) |
            Q(assistant=user) |
            (
                    Q(public=True) & Q(manufacturers__in=manufacturers_qs)
            )
        ).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        for lesson in context["lessons"]:
            lesson.is_contributor = (
                    lesson.owner == user or lesson.assistant.filter(pk=user.pk).exists()
            )

        return context


class LessonDetailView(DetailView):
    model = Lesson
    template_name = "moderations/lesson/lesson_detail.html"
    context_object_name = "lesson"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        context['materials'] = lesson.materials.all()

        # Добавляем обработанный материал с полем `original_filename` или `file.name`
        for material in context['materials']:
            material.display_name = material.original_filename or material.file.name

        # Десериализуем данные из JSON, хранящиеся в поле resources
        try:
            resources_data = json.loads(self.object.resources)  # Преобразуем строку JSON в объект Python
            context['questions'] = resources_data.get('questions', [])  # Получаем список вопросов
        except json.JSONDecodeError:
            context['questions'] = []  # Если JSON некорректный, выводим пустой список
            print("Ошибка при разборе JSON: в поле resources невалидные данные.")
        except Exception as e:
            context['questions'] = []
            print(f"Ошибка: {e}")

        # Проверяем, существует ли результат теста для текущего пользователя
        user = self.request.user
        if user.is_authenticated:
            test_result = TestResult.objects.filter(lesson=lesson, user=user).first()

            if not test_result:
                # Если результат теста не существует, создаем новый
                test_result = TestResult.objects.create(
                    lesson=lesson,
                    user=user,
                    score=0,  # Пока не вычислена оценка
                    total_questions=len(context['questions']),
                    correct_answers=0,
                    resources='[]'  # Пока пустые ответы
                )

            context['test_result'] = test_result

        return context


class LessonInitCreateRedirectView(View):
    def get(self, request, *args, **kwargs):
        # Создаём Lesson с минимально необходимыми значениями
        lesson = Lesson.objects.create(
            name="Новый урок",
            slug=str(uuid.uuid4())  # Временный уникальный slug
        )
        return redirect("moderation:lesson_edit", pk=lesson.pk)


class LessonEditView(UpdateView):
    model = Lesson
    form_class = LessonForm
    template_name = "moderations/lesson/lesson_form.html"
    pk_url_kwarg = "pk"
    success_url = reverse_lazy("moderation:lesson_list")  # ← нужный редирект

    def form_valid(self, form):
        if not form.instance.owner:
            form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lesson"] = self.object  # передаём lesson для JS
        # Получаем все LessonMaterial, относящиеся к текущему уроку
        context["materials"] = LessonMaterial.objects.filter(lesson=self.object)

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class LessonDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("moderation:lesson_list")

    def post(self, request):
        data = json.loads(request.body)
        faq_ids = data.get("faq_ids", [])
        if faq_ids:
            Lesson.objects.filter(id__in=faq_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


class ChunkUploadView(View):
    def post(self, request, *args, **kwargs):
        try:
            missing = []
            required_fields = ['lesson_id', 'file', 'filename', 'chunk_index', 'total_chunks']
            for field in required_fields:
                if field not in request.POST and field not in request.FILES:
                    missing.append(field)
            if missing:
                return JsonResponse({"success": False, "error": f"Missing fields: {missing}"}, status=400)

            lesson_id = request.POST["lesson_id"]
            chunk = request.FILES["file"]
            original_filename = request.POST["filename"]
            chunk_index = int(request.POST["chunk_index"])
            total_chunks = int(request.POST["total_chunks"])
            temp_file_id = request.POST.get("temp_file_id") or str(uuid.uuid4())
            total_size = int(request.POST.get("total_size", chunk.size))

            # Check if the lesson exists
            try:
                lesson = Lesson.objects.get(pk=lesson_id)
            except Lesson.DoesNotExist:
                return JsonResponse({"success": False, "error": "Lesson not found"}, status=400)

            # Define the file path and chunk storage directory
            lesson_dir = os.path.join(settings.MEDIA_ROOT, 'lesson_chunks', lesson_id)

            # Ensure that the lesson directory exists
            if not os.path.exists(lesson_dir):
                os.makedirs(lesson_dir)

            # Define the path for the current chunk
            chunk_path = os.path.join(lesson_dir, f"{chunk_index}.part")

            # Save the chunk to the lesson directory
            with open(chunk_path, 'wb') as temp_file:
                for chunk_data in chunk.chunks():
                    temp_file.write(chunk_data)

            # Check if all chunks are uploaded
            uploaded_chunks = len([f for f in os.listdir(lesson_dir) if f.endswith('.part')])
            if uploaded_chunks == total_chunks:
                # Combine the chunks into the final file
                final_file_name = f"{original_filename}"
                final_file_path = os.path.join(settings.MEDIA_ROOT, 'lesson', final_file_name)

                # Using FileSystemStorage to manage the file saving
                fs = FileSystemStorage(location=settings.MEDIA_ROOT)  # Correct storage location
                with fs.open(final_file_path, 'wb') as final_file:
                    for i in range(total_chunks):
                        chunk_part_path = os.path.join(lesson_dir, f"{i}.part")
                        with open(chunk_part_path, 'rb') as chunk_part:
                            final_file.write(chunk_part.read())
                        # Remove chunk part after adding to the final file
                        os.remove(chunk_part_path)

                # Create a LessonMaterial instance
                material = LessonMaterial(
                    lesson=lesson,
                    file=f"lesson/{final_file_name}",  # Correct relative URL for the file
                    original_filename=original_filename,
                    temp_file_id=temp_file_id,
                    size=total_size,
                    active=True
                )

                # Save the material object
                material.save()

                # Clean up the lesson directory
                os.rmdir(lesson_dir)

                return JsonResponse({"success": True, "message": "File uploaded successfully!"})
            else:
                return JsonResponse(
                    {"success": True, "message": "Chunk uploaded successfully, waiting for more chunks..."})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class DeleteMaterialView(View):
    def delete(self, request, *args, **kwargs):
        material_id = kwargs['material_id']
        try:
            # Получаем материал по ID
            material = get_object_or_404(LessonMaterial, id=material_id)
            # Удаляем файл с диска
            material.file.delete()
            # Удаляем запись из базы данных
            material.delete()
            return JsonResponse({"success": True}, status=200)
        except LessonMaterial.DoesNotExist:
            return JsonResponse({"success": False, "error": "Material not found"}, status=404)


# Email

def can_manage_emails(user):
    return user.is_superuser or user.has_perm('moderation.can_manage_emails')


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailTemplateListView(ListView):
    """Список шаблонов email"""
    model = EmailTemplate
    template_name = "moderations/email_templates_list.html"
    context_object_name = "templates"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        form = EmailTemplateFilterForm(self.request.GET)

        if form.is_valid():
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(subject__icontains=search) |
                    Q(slug__icontains=search)
                )

            category = form.cleaned_data.get('category')
            if category:
                queryset = queryset.filter(category=category)

            is_active = form.cleaned_data.get('is_active')
            if is_active == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active == 'false':
                queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = EmailTemplateFilterForm(self.request.GET)
        context['categories'] = EmailTemplate.CATEGORY_CHOICES
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailTemplateCreateView(CreateView):
    """Создание шаблона"""
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "moderations/email_template_form.html"
    success_url = reverse_lazy("moderation:email_templates")

    def form_valid(self, form):
        messages.success(self.request, "Шаблон успешно создан")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailTemplateUpdateView(UpdateView):
    """Редактирование шаблона"""
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "moderations/email_template_form.html"
    success_url = reverse_lazy("moderation:email_templates")

    def form_valid(self, form):
        messages.success(self.request, "Шаблон успешно обновлен")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailTemplateDeleteView(DeleteView):
    """Удаление шаблона"""
    model = EmailTemplate
    success_url = reverse_lazy("moderation:email_templates")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Шаблон успешно удален")
        return super().delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        template_ids = data.get("template_ids", [])
        if template_ids:
            EmailTemplate.objects.filter(id__in=template_ids).delete()
        return JsonResponse({"status": "success", "redirect": str(self.success_url)})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailTemplateDetailView(DetailView):
    """Детальный просмотр шаблона"""
    model = EmailTemplate
    template_name = "moderations/email_template_detail.html"
    context_object_name = "template"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class SendEmailView(View):
    """Отправка email"""

    def get(self, request):
        form = SendEmailForm()
        form.fields['user_group'].choices = [('', 'Выберите группу')] + [
            (group.id, group.name) for group in request.user.groups.all()
        ]
        return render(request, 'moderations/send_email.html', {'form': form})

    def post(self, request):
        form = SendEmailForm(request.POST, request.FILES)
        if form.is_valid():
            recipients = self.get_recipients(form.cleaned_data)

            subject = form.cleaned_data['subject']
            content = form.cleaned_data['content']
            template = form.cleaned_data.get('template')
            send_now = form.cleaned_data['send_now']
            scheduled_time = form.cleaned_data.get('scheduled_time')

            success_count = 0
            error_count = 0

            for recipient_email, recipient_name in recipients:
                # Замена переменных в шаблоне
                final_content = content
                final_subject = subject

                if template:
                    # Подстановка переменных
                    context = {
                        'username': recipient_name,
                        'email': recipient_email,
                        'site_name': settings.SITE_NAME,
                        'site_url': settings.SITE_URL,
                    }
                    final_content = template.content
                    final_subject = template.subject

                    # Замена переменных в шаблоне
                    for key, value in context.items():
                        final_content = final_content.replace(f'{{{{ {key} }}}}', str(value))
                        final_subject = final_subject.replace(f'{{{{ {key} }}}}', str(value))

                if send_now:
                    # Отправка сейчас
                    success = self.send_single_email(
                        recipient_email,
                        recipient_name,
                        final_subject,
                        final_content,
                        template,
                        request
                    )
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    # Добавление в очередь
                    self.add_to_queue(
                        recipient_email,
                        recipient_name,
                        final_subject,
                        final_content,
                        template,
                        scheduled_time
                    )
                    success_count += 1

            if send_now:
                messages.success(request, f"Письма отправлены: {success_count} успешно, {error_count} с ошибкой")
            else:
                messages.success(request, f"{success_count} писем добавлено в очередь на {scheduled_time}")

            return redirect('moderation:email_logs')

        return render(request, 'moderations/send_email.html', {'form': form})

    def get_recipients(self, data):
        """Получение списка получателей"""
        recipients = []
        recipient_type = data['recipient_type']

        if recipient_type == 'single':
            recipients.append((data['recipient_email'], ''))
        elif recipient_type == 'multiple':
            emails = data['recipient_emails'].split('\n')
            for email in emails:
                email = email.strip()
                if email:
                    recipients.append((email, ''))
        elif recipient_type == 'group' and data.get('user_group'):
            from django.contrib.auth.models import Group
            group = Group.objects.get(id=data['user_group'])
            for user in group.user_set.all():
                recipients.append((user.email, user.get_full_name() or user.username))

        return recipients

    def send_single_email(self, to_email, to_name, subject, content, template, request):
        """Отправка одного email"""
        try:
            from_email = settings.DEFAULT_FROM_EMAIL

            # Создание письма с HTML и текстовой версией
            msg = EmailMultiAlternatives(subject, content, from_email, [to_email])
            msg.attach_alternative(content, "text/html")

            # Отправка
            msg.send()

            # Логирование
            EmailLog.objects.create(
                recipient_email=to_email,
                recipient_name=to_name,
                subject=subject,
                template=template,
                content=content,
                status='sent',
                sent_at=timezone.now(),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            return True
        except Exception as e:
            # Логирование ошибки
            EmailLog.objects.create(
                recipient_email=to_email,
                recipient_name=to_name,
                subject=subject,
                template=template,
                content=content,
                status='failed',
                error_message=str(e)
            )
            return False

    def add_to_queue(self, to_email, to_name, subject, content, template, scheduled_time):
        """Добавление в очередь"""
        EmailQueue.objects.create(
            recipient_email=to_email,
            recipient_name=to_name,
            subject=subject,
            content=content,
            template=template,
            scheduled_for=scheduled_time
        )


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailLogListView(ListView):
    """Логи отправленных писем"""
    model = EmailLog
    template_name = "moderations/email_logs_list.html"
    context_object_name = "logs"
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()

        # Фильтрация
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(recipient_email__icontains=search) |
                Q(recipient_name__icontains=search) |
                Q(subject__icontains=search)
            )

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = EmailLog.STATUS_CHOICES

        # Статистика
        context['total_count'] = EmailLog.objects.count()
        context['sent_count'] = EmailLog.objects.filter(status='sent').count()
        context['failed_count'] = EmailLog.objects.filter(status='failed').count()
        context['opened_count'] = EmailLog.objects.filter(status='opened').count()

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailQueueListView(ListView):
    """Очередь писем"""
    model = EmailQueue
    template_name = "moderations/email_queue_list.html"
    context_object_name = "queue_items"
    paginate_by = 30

    def get_queryset(self):
        return EmailQueue.objects.filter(is_sent=False).order_by('-priority', 'scheduled_for')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_pending'] = EmailQueue.objects.filter(is_sent=False).count()
        context['total_sent'] = EmailQueue.objects.filter(is_sent=True).count()
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailQueueDeleteView(View):
    """Удаление из очереди"""

    def post(self, request):
        data = json.loads(request.body)
        queue_ids = data.get("queue_ids", [])
        if queue_ids:
            EmailQueue.objects.filter(id__in=queue_ids).delete()
        return JsonResponse({"status": "success"})


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class EmailLogDetailView(DetailView):
    """Детальный просмотр лога"""
    model = EmailLog
    template_name = "moderations/email_log_detail.html"
    context_object_name = "log"


@login_required
def preview_email_template(request, template_id):
    """Предпросмотр шаблона"""
    template = get_object_or_404(EmailTemplate, id=template_id)

    # Тестовые данные для предпросмотра
    context = {
        'username': 'Иван Иванов',
        'email': 'ivan@example.com',
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
        'confirmation_link': '#',
        'reset_link': '#',
        'order_number': 'ORD-12345',
        'order_total': '5000 ₽',
    }

    content = template.content
    subject = template.subject

    for key, value in context.items():
        content = content.replace(f'{{{{ {key} }}}}', str(value))
        subject = subject.replace(f'{{{{ {key} }}}}', str(value))

    return JsonResponse({
        'subject': subject,
        'content': content
    })


@login_required
def email_statistics(request):
    """Статистика email"""
    # Статистика по дням
    last_30_days = timezone.now() - timezone.timedelta(days=30)
    daily_stats = EmailLog.objects.filter(created_at__gte=last_30_days) \
        .extra({'day': "date(created_at)"}) \
        .values('day') \
        .annotate(
        total=models.Count('id'),
        sent=models.Count('id', filter=models.Q(status='sent')),
        failed=models.Count('id', filter=models.Q(status='failed')),
        opened=models.Count('id', filter=models.Q(status='opened'))
    ) \
        .order_by('day')

    # Статистика по шаблонам
    template_stats = EmailLog.objects.values('template__name') \
        .annotate(
        total=models.Count('id'),
        opened=models.Count('id', filter=models.Q(status='opened'))
    ) \
        .order_by('-total')[:10]

    # Статистика по статусам
    status_stats = EmailLog.objects.values('status') \
        .annotate(count=models.Count('id'))

    return JsonResponse({
        'daily_stats': list(daily_stats),
        'template_stats': list(template_stats),
        'status_stats': list(status_stats),
        'total_sent': EmailLog.objects.filter(status='sent').count(),
        'total_failed': EmailLog.objects.filter(status='failed').count(),
        'total_opened': EmailLog.objects.filter(status='opened').count(),
    })


# Функция для отправки писем из очереди (запускать через cron или celery)
def process_email_queue():
    """Обработка очереди писем"""
    now = timezone.now()
    pending_emails = EmailQueue.objects.filter(
        is_sent=False,
        scheduled_for__lte=now,
        attempts__lt=5  # Максимум 5 попыток
    ).order_by('-priority', 'scheduled_for')

    for email in pending_emails:
        try:
            from_email = settings.DEFAULT_FROM_EMAIL
            msg = EmailMultiAlternatives(email.subject, email.content, from_email, [email.recipient_email])
            msg.attach_alternative(email.content, "text/html")
            msg.send()

            email.is_sent = True
            email.sent_at = now
            email.save()

            # Логирование
            EmailLog.objects.create(
                recipient_email=email.recipient_email,
                recipient_name=email.recipient_name,
                subject=email.subject,
                template=email.template,
                content=email.content,
                status='sent',
                sent_at=now
            )
        except Exception as e:
            email.attempts += 1
            email.error = str(e)
            email.save()


@login_required
def send_test_email(request, template_id):
    """Отправка тестового письма"""
    if request.method == 'POST':
        template = get_object_or_404(EmailTemplate, id=template_id)
        email = request.POST.get('email')
        name = request.POST.get('name', 'Test User')

        try:
            # Подготовка контента
            context = {
                'username': name,
                'email': email,
                'site_name': settings.SITE_NAME,
                'site_url': settings.SITE_URL,
                'confirmation_link': '#',
                'reset_link': '#',
                'order_number': 'TEST-123',
                'order_total': '0 ₽',
            }

            content = template.content
            subject = template.subject

            for key, value in context.items():
                content = content.replace(f'{{{{ {key} }}}}', str(value))
                subject = subject.replace(f'{{{{ {key} }}}}', str(value))

            # Отправка
            msg = EmailMultiAlternatives(subject, content, settings.DEFAULT_FROM_EMAIL, [email])
            msg.attach_alternative(content, "text/html")
            msg.send()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def resend_email(request, log_id):
    """Повторная отправка письма"""
    if request.method == 'POST':
        log = get_object_or_404(EmailLog, id=log_id)

        try:
            msg = EmailMultiAlternatives(
                log.subject,
                log.content,
                settings.DEFAULT_FROM_EMAIL,
                [log.recipient_email]
            )
            msg.attach_alternative(log.content, "text/html")
            msg.send()

            # Обновление статуса
            log.status = 'sent'
            log.sent_at = timezone.now()
            log.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def delete_email_log(request, log_id):
    """Удаление лога"""
    if request.method == 'POST':
        log = get_object_or_404(EmailLog, id=log_id)
        log.delete()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Telephonia
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallDashboardView(TemplateView):
    """Дашборд телефонии"""
    template_name = "moderations/telephony/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # Основная статистика
        context['today_stats'] = CallRecord.objects.filter(
            start_time__date=today
        ).aggregate(
            total=Count('id'),
            answered=Count('id', filter=Q(status='answered')),
            missed=Count('id', filter=Q(status='missed')),
            avg_duration=Avg('duration')
        )

        context['week_stats'] = CallRecord.objects.filter(
            start_time__date__gte=week_ago
        ).aggregate(
            total=Count('id'),
            answered=Count('id', filter=Q(status='answered')),
            missed=Count('id', filter=Q(status='missed')),
            total_duration=Sum('duration')
        )

        # Последние звонки
        context['recent_calls'] = CallRecord.objects.select_related('caller', 'callee') \
            .order_by('-start_time')[:10]

        # Активные номера
        context['active_numbers'] = PhoneNumber.objects.filter(status='active').count()

        # Операторы онлайн
        context['online_operators'] = CallSettings.objects.filter(
            is_online=True,
            dnd_mode=False
        ).count()

        # Топ операторов
        context['top_operators'] = CallRecord.objects.filter(
            start_time__date__gte=week_ago,
            callee__isnull=False,
            status='answered'
        ).values('callee__username').annotate(
            total=Count('id'),
            total_duration=Sum('duration')
        ).order_by('-total')[:5]

        # Динамика звонков по часам (сегодня)
        hourly_stats = CallRecord.objects.filter(
            start_time__date=today
        ).annotate(
            hour=TruncHour('start_time')
        ).values('hour').annotate(
            total=Count('id'),
            inbound=Count('id', filter=Q(direction='inbound')),
            outbound=Count('id', filter=Q(direction='outbound'))
        ).order_by('hour')

        context['hourly_stats'] = list(hourly_stats)

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallRecordListView(ListView):
    """Список звонков"""
    model = CallRecord
    template_name = "moderations/telephony/call_list.html"
    context_object_name = "calls"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('caller', 'callee')

        # Фильтрация
        direction = self.request.GET.get('direction')
        if direction:
            queryset = queryset.filter(direction=direction)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        caller = self.request.GET.get('caller')
        if caller:
            queryset = queryset.filter(caller_number__icontains=caller)

        callee = self.request.GET.get('callee')
        if callee:
            queryset = queryset.filter(callee_number__icontains=callee)

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(start_time__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(start_time__date__lte=date_to)

        duration_min = self.request.GET.get('duration_min')
        if duration_min:
            queryset = queryset.filter(duration__gte=duration_min)

        duration_max = self.request.GET.get('duration_max')
        if duration_max:
            queryset = queryset.filter(duration__lte=duration_max)

        operator = self.request.GET.get('operator')
        if operator:
            queryset = queryset.filter(Q(caller_id=operator) | Q(callee_id=operator))

        return queryset.order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = CallFilterForm(self.request.GET)
        context['directions'] = CallRecord.DIRECTION_CHOICES
        context['statuses'] = CallRecord.STATUS_CHOICES
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallRecordDetailView(DetailView):
    """Детальная информация о звонке"""
    model = CallRecord
    template_name = "moderations/telephony/call_detail.html"
    context_object_name = "call"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['note_form'] = CallNoteForm(instance=self.object)

        # Получаем запись разговора
        try:
            context['recording'] = CallRecording.objects.get(call=self.object)
        except CallRecording.DoesNotExist:
            context['recording'] = None

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CallNoteForm(request.POST, instance=self.object)

        if form.is_valid():
            form.save()
            messages.success(request, "Заметка сохранена")
            return redirect('moderation:call_detail', pk=self.object.pk)

        context = self.get_context_data()
        context['note_form'] = form
        return self.render_to_response(context)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PhoneNumberListView(ListView):
    """Список телефонных номеров"""
    model = PhoneNumber
    template_name = "moderations/telephony/phone_numbers.html"
    context_object_name = "numbers"
    paginate_by = 20


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PhoneNumberCreateView(CreateView):
    """Создание телефонного номера"""
    model = PhoneNumber
    form_class = PhoneNumberForm
    template_name = "moderations/telephony/phone_number_form.html"
    success_url = reverse_lazy("moderation:phone_numbers")

    def form_valid(self, form):
        messages.success(self.request, "Номер успешно добавлен")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PhoneNumberUpdateView(UpdateView):
    """Редактирование телефонного номера"""
    model = PhoneNumber
    form_class = PhoneNumberForm
    template_name = "moderations/telephony/phone_number_form.html"
    success_url = reverse_lazy("moderation:phone_numbers")

    def form_valid(self, form):
        messages.success(self.request, "Номер успешно обновлен")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class PhoneNumberDeleteView(DeleteView):
    """Удаление телефонного номера"""
    model = PhoneNumber
    success_url = reverse_lazy("moderation:phone_numbers")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Номер удален")
        return super().delete(request, *args, **kwargs)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallQueueListView(ListView):
    """Список очередей"""
    model = CallQueue
    template_name = "moderations/telephony/queues.html"
    context_object_name = "queues"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallQueueCreateView(CreateView):
    """Создание очереди"""
    model = CallQueue
    form_class = CallQueueForm
    template_name = "moderations/telephony/queue_form.html"
    success_url = reverse_lazy("moderation:queues")


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VoiceMenuListView(ListView):
    """Список голосовых меню"""
    model = VoiceMenu
    template_name = "moderations/telephony/voice_menus.html"
    context_object_name = "menus"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallSettingsView(UpdateView):
    """Настройки телефонии пользователя"""
    model = CallSettings
    form_class = CallSettingsForm
    template_name = "moderations/telephony/settings.html"

    def get_object(self, queryset=None):
        obj, created = CallSettings.objects.get_or_create(user=self.request.user)
        return obj

    def get_success_url(self):
        return reverse_lazy("moderation:call_settings")

    def form_valid(self, form):
        messages.success(self.request, "Настройки сохранены")
        return super().form_valid(form)


@login_required
def make_call(request):
    """Совершить звонок"""
    if request.method == 'POST':
        form = QuickCallForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data['number']
            extension = form.cleaned_data.get('extension', '')

            # Здесь логика инициации звонка через API телефонии
            try:
                # Имитация звонка
                call = CallRecord.objects.create(
                    call_id=f"call_{timezone.now().timestamp()}",
                    direction='outbound',
                    status='answered',
                    caller=request.user,
                    caller_number=request.user.phone_settings.extension if hasattr(request.user,
                                                                                   'phone_settings') else '',
                    caller_name=request.user.get_full_name(),
                    callee_number=number,
                    callee_name='',
                    start_time=timezone.now(),
                    answer_time=timezone.now(),
                )

                messages.success(request, f"Звонок на номер {number} инициирован")
                return JsonResponse({'status': 'success', 'call_id': call.id})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def call_statistics(request):
    """Статистика звонков"""
    # Статистика по дням за последние 30 дней
    last_30_days = timezone.now() - timedelta(days=30)
    daily_stats = CallRecord.objects.filter(
        start_time__gte=last_30_days
    ).annotate(
        date=TruncDate('start_time')
    ).values('date').annotate(
        total=Count('id'),
        answered=Count('id', filter=Q(status='answered')),
        missed=Count('id', filter=Q(status='missed')),
        inbound=Count('id', filter=Q(direction='inbound')),
        outbound=Count('id', filter=Q(direction='outbound')),
        avg_duration=Avg('duration')
    ).order_by('date')

    # Статистика по операторам
    operator_stats = CallRecord.objects.filter(
        start_time__gte=last_30_days,
        status='answered'
    ).values('callee__username').annotate(
        total=Count('id'),
        total_duration=Sum('duration'),
        avg_duration=Avg('duration')
    ).order_by('-total')

    # Статистика по часам
    hourly_stats = CallRecord.objects.filter(
        start_time__gte=last_30_days
    ).annotate(
        hour=TruncHour('start_time')
    ).values('hour').annotate(
        total=Count('id')
    ).order_by('hour')

    return JsonResponse({
        'daily_stats': list(daily_stats),
        'operator_stats': list(operator_stats),
        'hourly_stats': list(hourly_stats),
    })


@login_required
def download_recording(request, call_id):
    """Скачать запись разговора"""
    recording = get_object_or_404(CallRecording, call_id=call_id)

    if recording.audio_file:
        recording.download_count += 1
        recording.is_downloaded = True
        recording.save()

        response = HttpResponse(recording.audio_file.read(), content_type='audio/mpeg')
        response['Content-Disposition'] = f'attachment; filename="call_{call_id}.{recording.file_format}"'
        return response

    return HttpResponse("Запись не найдена", status=404)


@login_required
def export_calls_csv(request):
    """Экспорт звонков в CSV"""
    queryset = CallRecord.objects.filter(
        start_time__date__gte=request.GET.get('date_from', '2024-01-01'),
        start_time__date__lte=request.GET.get('date_to', timezone.now().date())
    ).select_related('caller', 'callee')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="calls_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Дата', 'Направление', 'Статус', 'Звонящий', 'Получатель',
                     'Длительность', 'Ожидание', 'Стоимость', 'Заметки'])

    for call in queryset:
        writer.writerow([
            call.id,
            call.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            call.get_direction_display(),
            call.get_status_display(),
            f"{call.caller_name} ({call.caller_number})",
            f"{call.callee_name} ({call.callee_number})",
            call.get_duration_formatted(),
            call.get_wait_formatted(),
            call.cost,
            call.notes[:100]
        ])

    return response


@login_required
def set_operator_status(request):
    """Установить статус оператора"""
    if request.method == 'POST':
        settings, created = CallSettings.objects.get_or_create(user=request.user)

        status_type = request.POST.get('status')
        if status_type == 'online':
            settings.is_online = True
            settings.dnd_mode = False
        elif status_type == 'offline':
            settings.is_online = False
        elif status_type == 'dnd':
            settings.dnd_mode = True
        elif status_type == 'away':
            settings.away_message = request.POST.get('message', '')

        settings.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def get_operator_status(request):
    """Получить статус оператора"""
    settings, created = CallSettings.objects.get_or_create(user=request.user)

    status = 'online'
    if not settings.is_online:
        status = 'offline'
    elif settings.dnd_mode:
        status = 'dnd'

    return JsonResponse({
        'status': status,
        'away_message': settings.away_message if status == 'away' else ''
    })


@login_required
def queue_stats_api(request, pk):
    """API для получения статистики очереди"""
    queue = get_object_or_404(CallQueue, id=pk)

    # Получаем статистику за последние 30 дней
    last_30_days = timezone.now() - timedelta(days=30)
    daily_stats = CallRecord.objects.filter(
        callee_number=queue.extension,
        start_time__gte=last_30_days
    ).annotate(
        date=TruncDate('start_time')
    ).values('date').annotate(
        total=Count('id'),
        answered=Count('id', filter=Q(status='answered')),
        missed=Count('id', filter=Q(status='missed'))
    ).order_by('date')

    return JsonResponse({
        'name': queue.name,
        'total_calls': queue.total_calls,
        'answered_calls': queue.answered_calls,
        'missed_calls': queue.missed_calls,
        'daily_stats': list(daily_stats)
    })


@login_required
def menu_structure_api(request, pk):
    """API для получения структуры голосового меню"""
    menu = get_object_or_404(VoiceMenu, id=pk)

    return JsonResponse({
        'name': menu.name,
        'greeting_message': menu.greeting_message,
        'menu_items': menu.menu_items,
        'timeout': menu.timeout,
        'max_retries': menu.max_retries
    })


@login_required
def reset_call_settings(request):
    """Сброс настроек телефонии"""
    if request.method == 'POST':
        settings, created = CallSettings.objects.get_or_create(user=request.user)
        settings.extension = ''
        settings.mobile_forward = ''
        settings.email_forward = ''
        settings.notify_on_call = True
        settings.notify_on_missed = True
        settings.notify_by_email = True
        settings.notify_by_sms = False
        settings.auto_record = True
        settings.record_outbound = True
        settings.record_inbound = True
        settings.work_start = '09:00'
        settings.work_end = '18:00'
        settings.work_days = [1, 2, 3, 4, 5]
        settings.is_online = True
        settings.dnd_mode = False
        settings.away_message = ''
        settings.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallQueueListView(ListView):
    """Список очередей"""
    model = CallQueue
    template_name = "moderations/telephony/queues.html"
    context_object_name = "queues"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Подсчет общего количества операторов
        total_members = 0
        for queue in context['queues']:
            total_members += queue.members.count()
        context['total_members'] = total_members

        # Среднее время ожидания
        avg_wait_time = CallRecord.objects.filter(
            status='answered',
            wait_duration__gt=0
        ).aggregate(avg=Avg('wait_duration'))['avg']
        context['avg_wait_time'] = avg_wait_time or 0

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallQueueCreateView(CreateView):
    """Создание очереди"""
    model = CallQueue
    form_class = CallQueueForm
    template_name = "moderations/telephony/queue_form.html"
    success_url = reverse_lazy("moderation:queues")

    def form_valid(self, form):
        messages.success(self.request, "Очередь успешно создана")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallQueueUpdateView(UpdateView):
    """Редактирование очереди"""
    model = CallQueue
    form_class = CallQueueForm
    template_name = "moderations/telephony/queue_form.html"
    success_url = reverse_lazy("moderation:queues")

    def form_valid(self, form):
        messages.success(self.request, "Очередь успешно обновлена")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class CallQueueDeleteView(DeleteView):
    """Удаление очереди"""
    model = CallQueue
    success_url = reverse_lazy("moderation:queues")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Очередь удалена")
        return super().delete(request, *args, **kwargs)


# ========== Голосовые меню (IVR) ==========

@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VoiceMenuListView(ListView):
    """Список голосовых меню"""
    model = VoiceMenu
    template_name = "moderations/telephony/voice_menus.html"
    context_object_name = "menus"


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VoiceMenuCreateView(CreateView):
    """Создание голосового меню"""
    model = VoiceMenu
    form_class = VoiceMenuForm
    template_name = "moderations/telephony/voice_menu_form.html"
    success_url = reverse_lazy("moderation:voice_menus")

    def form_valid(self, form):
        messages.success(self.request, "Голосовое меню успешно создано")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VoiceMenuUpdateView(UpdateView):
    """Редактирование голосового меню"""
    model = VoiceMenu
    form_class = VoiceMenuForm
    template_name = "moderations/telephony/voice_menu_form.html"
    success_url = reverse_lazy("moderation:voice_menus")

    def form_valid(self, form):
        messages.success(self.request, "Голосовое меню успешно обновлено")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class VoiceMenuDeleteView(DeleteView):
    """Удаление голосового меню"""
    model = VoiceMenu
    success_url = reverse_lazy("moderation:voice_menus")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Голосовое меню удалено")
        return super().delete(request, *args, **kwargs)


# ========== API функции ==========

@login_required
def queue_stats_api(request, pk):
    """API для получения статистики очереди"""
    queue = get_object_or_404(CallQueue, id=pk)

    # Получаем статистику за последние 30 дней
    from django.db.models.functions import TruncDate
    from django.db.models import Count, Q

    last_30_days = timezone.now() - timedelta(days=30)
    daily_stats = CallRecord.objects.filter(
        callee_number=queue.extension,
        start_time__gte=last_30_days
    ).annotate(
        date=TruncDate('start_time')
    ).values('date').annotate(
        total=Count('id'),
        answered=Count('id', filter=Q(status='answered')),
        missed=Count('id', filter=Q(status='missed'))
    ).order_by('date')

    # Форматируем даты
    daily_list = []
    for stat in daily_stats:
        daily_list.append({
            'date': stat['date'].strftime('%Y-%m-%d') if stat['date'] else None,
            'total': stat['total'],
            'answered': stat['answered'],
            'missed': stat['missed']
        })

    return JsonResponse({
        'name': queue.name,
        'total_calls': queue.total_calls,
        'answered_calls': queue.answered_calls,
        'missed_calls': queue.missed_calls,
        'daily_stats': daily_list
    })


@login_required
def menu_structure_api(request, pk):
    """API для получения структуры голосового меню"""
    menu = get_object_or_404(VoiceMenu, id=pk)

    return JsonResponse({
        'name': menu.name,
        'greeting_message': menu.greeting_message,
        'menu_items': menu.menu_items,
        'timeout': menu.timeout,
        'max_retries': menu.max_retries
    })


@login_required
def reset_call_settings(request):
    """Сброс настроек телефонии"""
    if request.method == 'POST':
        settings, created = CallSettings.objects.get_or_create(user=request.user)
        settings.extension = ''
        settings.mobile_forward = ''
        settings.email_forward = ''
        settings.notify_on_call = True
        settings.notify_on_missed = True
        settings.notify_by_email = True
        settings.notify_by_sms = False
        settings.auto_record = True
        settings.record_outbound = True
        settings.record_inbound = True
        settings.work_start = '09:00'
        settings.work_end = '18:00'
        settings.work_days = [1, 2, 3, 4, 5]
        settings.is_online = True
        settings.dnd_mode = False
        settings.away_message = ''
        settings.save()

        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


method_decorator(login_required(login_url="moderation:login"), name="dispatch")


class IntegrationsDashboardView(TemplateView):
    """Дашборд интеграций"""
    template_name = "moderations/integrations/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Статистика по типам
        context['stats'] = {
            'total': IntegrationService.objects.count(),
            'active': IntegrationService.objects.filter(is_active=True).count(),
            'marketplace': IntegrationService.objects.filter(service_type='marketplace').count(),
            'payment': IntegrationService.objects.filter(service_type='payment').count(),
            'delivery': IntegrationService.objects.filter(service_type='delivery').count(),
            'messenger': IntegrationService.objects.filter(service_type='messenger').count(),
            'additional': IntegrationService.objects.filter(service_type='additional').count(),
        }

        # Последние логи
        context['recent_logs'] = IntegrationLog.objects.select_related('integration')[:10]

        # Активные интеграции
        context['active_integrations'] = IntegrationService.objects.filter(is_active=True)[:8]

        # Статистика синхронизации за последние 7 дней
        last_week = timezone.now() - timedelta(days=7)
        context['sync_stats'] = IntegrationLog.objects.filter(
            started_at__gte=last_week,
            operation__startswith='sync'
        ).values('operation').annotate(
            total=Count('id'),
            success=Count('id', filter=Q(status='success')),
            error=Count('id', filter=Q(status='error'))
        )

        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class IntegrationListView(ListView):
    """Список интеграций"""
    model = IntegrationService
    template_name = "moderations/integrations/list.html"
    context_object_name = "integrations"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        service_type = self.request.GET.get('type')
        if service_type:
            queryset = queryset.filter(service_type=service_type)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )

        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('service_type', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_types'] = IntegrationService.SERVICE_TYPES
        context['active_filters'] = {
            'type': self.request.GET.get('type', ''),
            'search': self.request.GET.get('search', ''),
            'status': self.request.GET.get('status', ''),
        }
        return context


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class IntegrationCreateView(CreateView):
    """Создание интеграции"""
    model = IntegrationService
    form_class = IntegrationServiceForm
    template_name = "moderations/integrations/form.html"
    success_url = reverse_lazy("moderation:integrations")

    def form_valid(self, form):
        messages.success(self.request, f"Интеграция '{form.instance.name}' успешно создана")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class IntegrationUpdateView(UpdateView):
    """Редактирование интеграции"""
    model = IntegrationService
    form_class = IntegrationServiceForm
    template_name = "moderations/integrations/form.html"
    success_url = reverse_lazy("moderation:integrations")

    def form_valid(self, form):
        messages.success(self.request, f"Интеграция '{form.instance.name}' успешно обновлена")
        return super().form_valid(form)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class IntegrationDeleteView(DeleteView):
    """Удаление интеграции"""
    model = IntegrationService
    success_url = reverse_lazy("moderation:integrations")

    def delete(self, request, *args, **kwargs):
        integration = self.get_object()
        messages.success(request, f"Интеграция '{integration.name}' удалена")
        return super().delete(request, *args, **kwargs)


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class IntegrationDetailView(DetailView):
    """Детальная информация об интеграции"""
    model = IntegrationService
    template_name = "moderations/integrations/detail.html"
    context_object_name = "integration"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Логи интеграции
        context['logs'] = IntegrationLog.objects.filter(
            integration=self.object
        )[:20]

        # Статистика по типу
        if self.object.service_type == 'marketplace':
            context['products_count'] = MarketplaceProduct.objects.filter(
                marketplace=self.object
            ).count()
            context['orders_count'] = MarketplaceOrder.objects.filter(
                marketplace=self.object
            ).count()
        elif self.object.service_type == 'payment':
            try:
                context['payment_settings'] = PaymentIntegration.objects.get(
                    integration=self.object
                )
            except PaymentIntegration.DoesNotExist:
                context['payment_settings'] = None
            context['transactions_count'] = PaymentTransaction.objects.filter(
                payment=self.object
            ).count()
        elif self.object.service_type == 'delivery':
            try:
                context['delivery_settings'] = DeliveryIntegration.objects.get(
                    integration=self.object
                )
            except DeliveryIntegration.DoesNotExist:
                context['delivery_settings'] = None
            context['delivery_orders_count'] = DeliveryOrder.objects.filter(
                delivery=self.object
            ).count()
        elif self.object.service_type == 'messenger':
            try:
                context['messenger_settings'] = MessengerIntegration.objects.get(
                    integration=self.object
                )
            except MessengerIntegration.DoesNotExist:
                context['messenger_settings'] = None
            context['messages_count'] = MessengerMessage.objects.filter(
                messenger=self.object
            ).count()

        return context


@login_required
def integration_settings(request, pk):
    """Настройки интеграции в зависимости от типа"""
    integration = get_object_or_404(IntegrationService, pk=pk)

    if integration.service_type == 'marketplace':
        form = MarketplaceSettingsForm(instance=integration)
        template = 'moderations/integrations/marketplace_settings.html'
    elif integration.service_type == 'payment':
        payment_settings, created = PaymentIntegration.objects.get_or_create(
            integration=integration
        )
        form = PaymentSettingsForm(instance=payment_settings)
        template = 'moderations/integrations/payment_settings.html'
    elif integration.service_type == 'delivery':
        delivery_settings, created = DeliveryIntegration.objects.get_or_create(
            integration=integration
        )
        form = DeliverySettingsForm(instance=delivery_settings)
        template = 'moderations/integrations/delivery_settings.html'
    elif integration.service_type == 'messenger':
        messenger_settings, created = MessengerIntegration.objects.get_or_create(
            integration=integration
        )
        form = MessengerSettingsForm(instance=messenger_settings)
        template = 'moderations/integrations/messenger_settings.html'
    else:
        additional_settings, created = AdditionalService.objects.get_or_create(
            integration=integration
        )
        form = AdditionalServiceForm(instance=additional_settings)
        template = 'moderations/integrations/additional_settings.html'

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, "Настройки успешно сохранены")
            return redirect('moderation:integration_detail', pk=integration.pk)

    return render(request, template, {
        'integration': integration,
        'form': form
    })


@login_required
def test_integration(request, pk):
    """Тестирование подключения к интеграции"""
    if request.method == 'POST':
        integration = get_object_or_404(IntegrationService, pk=pk)

        # Здесь должна быть логика тестирования подключения
        # Для каждого типа интеграции свой тест

        # Имитация тестирования
        is_successful = True

        if is_successful:
            IntegrationLog.objects.create(
                integration=integration,
                operation='webhook',
                status='success',
                request_data={'test': True},
                response_data={'message': 'Connection successful'},
                duration=0.5,
                completed_at=timezone.now()
            )
            return JsonResponse({'status': 'success', 'message': 'Подключение успешно'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Ошибка подключения'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def sync_products(request):
    """Синхронизация товаров с маркетплейсом"""
    if request.method == 'POST':
        form = SyncProductsForm(request.POST)
        if form.is_valid():
            marketplace = form.cleaned_data['marketplace']
            sync_type = form.cleaned_data['sync_type']

            # Создаем лог
            log = IntegrationLog.objects.create(
                integration=marketplace,
                operation='sync_products',
                status='pending',
                request_data={'sync_type': sync_type},
                started_at=timezone.now()
            )

            # Здесь должна быть асинхронная задача на синхронизацию
            # Для примера - синхронная обработка

            try:
                # Имитация синхронизации
                products_synced = 0
                log.status = 'success'
                log.response_data = {'products_synced': products_synced}
                log.completed_at = timezone.now()
                log.duration = 1.5
                log.save()

                messages.success(request, f"Синхронизация завершена. Синхронизировано товаров: {products_synced}")
            except Exception as e:
                log.status = 'error'
                log.error_message = str(e)
                log.completed_at = timezone.now()
                log.save()
                messages.error(request, f"Ошибка синхронизации: {str(e)}")

            return redirect('moderation:integration_detail', pk=marketplace.pk)

    return redirect('moderation:integrations')


@login_required
def integration_logs(request, pk=None):
    """Просмотр логов интеграции"""
    logs = IntegrationLog.objects.select_related('integration')

    integration = None
    if pk:
        try:
            integration = get_object_or_404(IntegrationService, pk=pk)
            logs = logs.filter(integration=integration)
        except IntegrationService.DoesNotExist:
            # Если интеграция удалена, показываем все логи
            pass

    # Фильтрация
    operation = request.GET.get('operation')
    if operation:
        logs = logs.filter(operation=operation)

    status = request.GET.get('status')
    if status:
        logs = logs.filter(status=status)

    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(started_at__date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(started_at__date__lte=date_to)

    # Пагинация
    paginator = Paginator(logs, 30)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)

    # Получаем уникальные интеграции для фильтра
    integrations = IntegrationService.objects.filter(
        id__in=logs.values_list('integration_id', flat=True).distinct()
    )

    return render(request, 'moderations/integrations/logs.html', {
        'logs': logs_page,
        'integration': integration,
        'integrations': integrations,
        'operations': IntegrationLog.OPERATION_TYPES,
        'statuses': [('success', 'Успех'), ('error', 'Ошибка'), ('pending', 'В процессе')],
        'filters': {
            'operation': operation,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    })


@login_required
def webhook_handler(request, code):
    """Обработчик webhook для интеграции"""
    try:
        integration = IntegrationService.objects.get(code=code, is_active=True)
    except IntegrationService.DoesNotExist:
        return JsonResponse({'error': 'Integration not found'}, status=404)

    # Получаем данные из запроса
    if request.method == 'POST':
        data = json.loads(request.body)

        # Создаем лог
        log = IntegrationLog.objects.create(
            integration=integration,
            operation='webhook',
            status='pending',
            request_data=data,
            started_at=timezone.now()
        )

        try:
            # Обработка webhook в зависимости от типа интеграции
            # Здесь должна быть логика обработки

            log.status = 'success'
            log.completed_at = timezone.now()
            log.save()

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            log.status = 'error'
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.save()

            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def marketplace_products(request, pk):
    """Список товаров маркетплейса"""
    integration = get_object_or_404(IntegrationService, pk=pk, service_type='marketplace')
    products = MarketplaceProduct.objects.filter(marketplace=integration)

    # Фильтрация
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(marketplace_sku__icontains=search) |
            Q(product__name__icontains=search)
        )

    status = request.GET.get('status')
    if status:
        products = products.filter(status=status)

    # Пагинация
    paginator = Paginator(products, 30)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)

    return render(request, 'moderations/integrations/marketplace_products.html', {
        'integration': integration,
        'products': products_page,
        'statuses': [('active', 'Активен'), ('inactive', 'Неактивен'), ('archived', 'Архивирован')],
    })


@login_required
def marketplace_orders(request, pk):
    """Список заказов маркетплейса"""
    integration = get_object_or_404(IntegrationService, pk=pk, service_type='marketplace')
    orders = MarketplaceOrder.objects.filter(marketplace=integration).order_by('-order_date')

    # Фильтрация
    search = request.GET.get('search')
    if search:
        orders = orders.filter(marketplace_order_id__icontains=search)

    sync_status = request.GET.get('sync_status')
    if sync_status:
        orders = orders.filter(sync_status=sync_status)

    date_from = request.GET.get('date_from')
    if date_from:
        orders = orders.filter(order_date__date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        orders = orders.filter(order_date__date__lte=date_to)

    # Пагинация
    paginator = Paginator(orders, 30)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)

    return render(request, 'moderations/integrations/marketplace_orders.html', {
        'integration': integration,
        'orders': orders_page,
        'sync_statuses': [('pending', 'Ожидает'), ('synced', 'Синхронизирован'), ('error', 'Ошибка')],
    })


@login_required
def payment_transactions(request, pk):
    """Список платежных транзакций"""
    integration = get_object_or_404(IntegrationService, pk=pk, service_type='payment')
    transactions = PaymentTransaction.objects.filter(payment=integration).order_by('-created_at')

    # Фильтрация
    status = request.GET.get('status')
    if status:
        transactions = transactions.filter(status=status)

    date_from = request.GET.get('date_from')
    if date_from:
        transactions = transactions.filter(created_at__date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        transactions = transactions.filter(created_at__date__lte=date_to)

    # Пагинация
    paginator = Paginator(transactions, 30)
    page = request.GET.get('page')
    transactions_page = paginator.get_page(page)

    return render(request, 'moderations/integrations/payment_transactions.html', {
        'integration': integration,
        'transactions': transactions_page,
        'statuses': PaymentTransaction.STATUS_CHOICES,
    })


@login_required
def delivery_orders(request, pk):
    """Список заказов доставки"""
    integration = get_object_or_404(IntegrationService, pk=pk, service_type='delivery')
    orders = DeliveryOrder.objects.filter(delivery=integration).order_by('-created_at')

    # Фильтрация
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    tracking = request.GET.get('tracking')
    if tracking:
        orders = orders.filter(tracking_number__icontains=tracking)

    # Пагинация
    paginator = Paginator(orders, 30)
    page = request.GET.get('page')
    orders_page = paginator.get_page(page)

    return render(request, 'moderations/integrations/delivery_orders.html', {
        'integration': integration,
        'orders': orders_page,
        'statuses': DeliveryOrder.STATUS_CHOICES,
    })


@login_required
def messenger_messages(request, pk):
    """Список сообщений мессенджера"""
    integration = get_object_or_404(IntegrationService, pk=pk, service_type='messenger')
    messages = MessengerMessage.objects.filter(messenger=integration).order_by('-created_at')

    # Фильтрация
    direction = request.GET.get('direction')
    if direction:
        messages = messages.filter(direction=direction)

    is_read = request.GET.get('is_read')
    if is_read:
        messages = messages.filter(is_read=(is_read == 'true'))

    # Пагинация
    paginator = Paginator(messages, 30)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)

    return render(request, 'moderations/integrations/messenger_messages.html', {
        'integration': integration,
        'messages': messages_page,
        'directions': [('inbound', 'Входящие'), ('outbound', 'Исходящие')],
    })


@login_required
def log_details_api(request, log_id):
    """API для получения деталей лога"""
    log = get_object_or_404(IntegrationLog, id=log_id)

    return JsonResponse({
        'id': log.id,
        'integration_id': log.integration.id,
        'integration_name': log.integration.name,
        'operation': log.operation,
        'operation_display': log.get_operation_display(),
        'status': log.status,
        'status_display': log.get_status_display(),
        'request_data': log.request_data,
        'response_data': log.response_data,
        'error_message': log.error_message,
        'duration': log.duration,
        'duration_formatted': log.get_duration_formatted(),
        'started_at': log.started_at.strftime('%d.%m.%Y %H:%M:%S'),
        'completed_at': log.completed_at.strftime('%d.%m.%Y %H:%M:%S') if log.completed_at else None,
    })


@login_required
@require_http_methods(["POST"])
def sync_all_integrations(request):
    """Синхронизация всех интеграций"""
    out = io.StringIO()

    try:
        call_command('sync_integrations', stdout=out)
        output = out.getvalue()

        success_count = output.count('Успешно')
        error_count = output.count('Ошибка')

        return JsonResponse({
            'status': 'success',
            'success_count': success_count,
            'error_count': error_count,
            'output': output
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)