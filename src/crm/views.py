from django.db import models
from django.views.generic import (
    ListView,
    UpdateView,
    DeleteView,
    View,
)
from django.urls import reverse_lazy
from .models import Lead, Leaddocement, Note, Task, StatusPayment, Deal
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from .forms import LeadForm
from useraccount.models import Profile
from django.http import JsonResponse
from urllib.parse import unquote as urlunquote
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from django.db.models import Sum, Max
from django.utils import timezone
from datetime import datetime
from django.utils.dateformat import format
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods


@require_POST
@login_required
def update_task_status(request):
    try:
        task_id = int(request.POST.get("task_id", 0))
        new_status = request.POST.get("new_status")

        if not task_id or not new_status:
            return JsonResponse({"success": False, "error": "Недостаточно данных"})

        task = Task.objects.get(id=task_id)  # убрали проверку assigned_to
        task.type = new_status
        task.save()
        return JsonResponse({"success": True, "new_status": task.get_type_display()})
    except Task.DoesNotExist:
        return JsonResponse({"success": False, "error": "Задача не найдена"})
    except ValueError:
        return JsonResponse({"success": False, "error": "Некорректный ID задачи"})


class UserTaskListView(ListView):
    model = Task
    template_name = "moderations/leads/task.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user)


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = "moderations/leads/lead_list.html"
    context_object_name = "leads"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_count = Lead.objects.count()
        count_passed = Lead.objects.filter(status="passed").count()

        context["total_count"] = total_count
        context["count_at_work"] = Lead.objects.filter(status="at_work").count()
        context["count_passed"] = count_passed
        context["count_lost"] = Lead.objects.filter(status="lost").count()

        # Проценты
        if total_count > 0:
            percent_passed = (count_passed / total_count) * 100
            percent_not_passed = 100 - percent_passed
        else:
            percent_passed = 0
            percent_not_passed = 0

        context["percent_passed"] = round(percent_passed, 2)
        context["percent_not_passed"] = round(percent_not_passed, 2)

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

        return context


@csrf_exempt  # Или используйте @login_required + csrfmiddlewaretoken
@login_required
def update_lead_status(request, pk):
    if request.method == "POST":
        lead = get_object_or_404(Lead, pk=pk)
        new_status = request.POST.get("status")
        if new_status in dict(Lead.STATUS_CHOICES):
            lead.status = new_status
            lead.save()
            return JsonResponse({"success": True, "new_status": new_status})
        return JsonResponse({"success": False, "error": "Недопустимый статус"})
    return JsonResponse({"success": False, "error": "Только POST-запросы"})


@require_POST
@csrf_exempt  # Убери, если используешь нормальный CSRF
def delete_single_lead_ajax(request, pk):
    try:
        lead = Lead.objects.get(pk=pk)
        lead.delete()
        return JsonResponse({"success": True})
    except Lead.DoesNotExist:
        return JsonResponse({"success": False, "error": "Лид не найден"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


class LeadCreateRedirectView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        lead = Lead.objects.create(
            client=request.user,
            amount=0,
            paid_out=0,
            swim_out=0,
            expenditure=0,
            profit=0,
        )
        return redirect("crm:lead_update", pk=lead.pk)


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "moderations/leads/lead_form.html"
    context_object_name = "lead"

    def get_success_url(self):
        return reverse("crm:lead_update", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients"] = Profile.objects.filter(type=4)
        context["users_worker"] = Profile.objects.filter(type=0)

        phone = self.request.GET.get("phone")
        if (
            phone
            and not self.request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            client = self.get_client_by_phone(phone)
            context["client_data"] = client

        return context

    def get(self, request, *args, **kwargs):
        phone = request.GET.get("phone")
        if request.headers.get("x-requested-with") == "XMLHttpRequest" and phone:
            return self.phone_search(phone)
        return super().get(request, *args, **kwargs)

    def phone_search(self, phone):
        client = self.get_client_by_phone(phone)
        if client:
            return JsonResponse(
                {
                    "id": str(client.id),
                    "full_name": client.get_full_name(),
                    "phone": client.phone,
                }
            )
        return JsonResponse({"error": "Клиент не найден"})

    def get_client_by_phone(self, phone):
        phone = urlunquote(phone.strip())
        if not phone:
            return None
        try:
            return Profile.objects.get(phone=phone, type=4)
        except Profile.DoesNotExist:
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        phone = self.request.GET.get("phone")
        if (
            phone
            and not self.request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            client = self.get_client_by_phone(phone)
            if client:
                kwargs.setdefault("initial", {})["client"] = str(client.id)
        return kwargs

    def form_valid(self, form):
        print("Form cleaned data: ", form.cleaned_data)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form errors: ", form.errors)
        return super().form_invalid(form)


@csrf_exempt
@require_POST
def update_task_position(request):
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_position = data.get('position')

        task = Task.objects.get(id=task_id)

        # Получаем все задачи в этом лиде
        siblings = Task.objects.filter(lead=task.lead).exclude(id=task_id)

        # Корректируем позиции
        if task.position > new_position:
            # Перемещаем вверх
            siblings.filter(
                position__gte=new_position,
                position__lt=task.position
            ).update(position=models.F('position') + 1)
        else:
            # Перемещаем вниз
            siblings.filter(
                position__gt=task.position,
                position__lte=new_position
            ).update(position=models.F('position') - 1)

        task.position = new_position
        task.save()

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
@require_POST
def add_subdeal(request):
    try:
        data = json.loads(request.body)
        parent_id = data.get('parent_id')
        title = data.get('title')

        parent_deal = Deal.objects.get(id=parent_id)

        # Определяем позицию для новой сделки
        max_position = Deal.objects.filter(parent=parent_deal).aggregate(Max('position'))['position__max'] or 0

        new_deal = Deal.objects.create(
            title=title,
            task=parent_deal.task,
            parent=parent_deal,
            position=max_position + 1
        )

        return JsonResponse({'status': 'success', 'deal_id': new_deal.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
@require_POST
def update_deal_position(request):
    try:
        data = json.loads(request.body)
        deal_id = data.get('deal_id')
        new_position = data.get('position')
        parent_id = data.get('parent_id')  # ID родительской сделки
        task_id = data.get('task_id')  # ID задачи, если сделка перемещается между задачами

        deal = Deal.objects.get(id=deal_id)

        # Если сделка перемещается к новой задаче
        if task_id and task_id != deal.task.id:
            new_task = Task.objects.get(id=task_id)
            deal.task = new_task
            deal.save()

        # Если сделка перемещается к новому родителю
        if parent_id:
            parent_deal = Deal.objects.get(id=parent_id)
            deal.parent = parent_deal
        else:
            deal.parent = None

        # Обновляем позиции всех сделок на том же уровне
        if deal.parent:
            siblings = Deal.objects.filter(parent=deal.parent).exclude(id=deal_id)
        else:
            siblings = Deal.objects.filter(parent__isnull=True, task=deal.task).exclude(id=deal_id)

        # Корректируем позиции
        if deal.position > new_position:
            # Перемещаем вверх
            siblings.filter(
                position__gte=new_position,
                position__lt=deal.position
            ).update(position=models.F('position') + 1)
        else:
            # Перемещаем вниз
            siblings.filter(
                position__gt=deal.position,
                position__lte=new_position
            ).update(position=models.F('position') - 1)

        deal.position = new_position
        deal.save()

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@method_decorator(csrf_exempt, name="dispatch")
class CreateStatusPaymentAjaxView(View):
    def post(self, request, *args, **kwargs):
        lead_id = request.POST.get("lead_id")
        amount = request.POST.get("amount", "Без сумму")
        description = request.POST.get("description", "")
        status = request.POST.get("status", "replenishment")

        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return JsonResponse({"error": "Лид не найден"}, status=404)

        payment = StatusPayment.objects.create(
            amount=amount, description=description, status=status
        )
        lead.payment.add(payment)

        return JsonResponse(
            {
                "message": "Платеж создан",
                "amount": payment.amount,
                "description": payment.description,
                "status": payment.status,
                "created_at": format(payment.created_at, "d.m.Y H:i"),
            }
        )


class LeadDocumentView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "moderations/leads/lead_document.html"
    context_object_name = "lead"

    def get_success_url(self):
        return reverse("crm:lead_document", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients"] = Profile.objects.filter(type=4)
        context["users_worker"] = Profile.objects.filter(type=0)

        phone = self.request.GET.get("phone")
        if (
            phone
            and not self.request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            client = self.get_client_by_phone(phone)
            context["client_data"] = client

        return context

    def get(self, request, *args, **kwargs):
        phone = request.GET.get("phone")
        if request.headers.get("x-requested-with") == "XMLHttpRequest" and phone:
            return self.phone_search(phone)
        return super().get(request, *args, **kwargs)

    def phone_search(self, phone):
        client = self.get_client_by_phone(phone)
        if client:
            return JsonResponse(
                {
                    "id": str(client.id),
                    "full_name": client.get_full_name(),
                    "phone": client.phone,
                }
            )
        return JsonResponse({"error": "Клиент не найден"})

    def get_client_by_phone(self, phone):
        phone = urlunquote(phone.strip())
        if not phone:
            return None
        try:
            return Profile.objects.get(phone=phone, type=4)
        except Profile.DoesNotExist:
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        phone = self.request.GET.get("phone")
        if (
            phone
            and not self.request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            client = self.get_client_by_phone(phone)
            if client:
                kwargs.setdefault("initial", {})["client"] = str(client.id)
        return kwargs

    def form_valid(self, form):
        print("Form cleaned data: ", form.cleaned_data)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form errors: ", form.errors)
        return super().form_invalid(form)


class LeadTaskView(LoginRequiredMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = "moderations/leads/lead_task.html"
    context_object_name = "lead"

    def get_success_url(self):
        return reverse("crm:lead_task", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clients"] = Profile.objects.filter(type=4)
        context["users_worker"] = Profile.objects.filter(type=0)

        phone = self.request.GET.get("phone")
        if (
            phone
            and not self.request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            client = self.get_client_by_phone(phone)
            context["client_data"] = client

        return context

    def get(self, request, *args, **kwargs):
        phone = request.GET.get("phone")
        if request.headers.get("x-requested-with") == "XMLHttpRequest" and phone:
            return self.phone_search(phone)
        return super().get(request, *args, **kwargs)

    def phone_search(self, phone):
        client = self.get_client_by_phone(phone)
        if client:
            return JsonResponse(
                {
                    "id": str(client.id),
                    "full_name": client.get_full_name(),
                    "phone": client.phone,
                }
            )
        return JsonResponse({"error": "Клиент не найден"})

    def get_client_by_phone(self, phone):
        phone = urlunquote(phone.strip())
        if not phone:
            return None
        try:
            return Profile.objects.get(phone=phone, type=4)
        except Profile.DoesNotExist:
            return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        phone = self.request.GET.get("phone")
        if (
            phone
            and not self.request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            client = self.get_client_by_phone(phone)
            if client:
                kwargs.setdefault("initial", {})["client"] = str(client.id)
        return kwargs

    def form_valid(self, form):
        print("Form cleaned data: ", form.cleaned_data)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form errors: ", form.errors)
        return super().form_invalid(form)


User = get_user_model()


@csrf_exempt
@require_POST
def create_task_and_deals(request):
    try:
        data = json.loads(request.body)

        # Создаем Task
        task = Task.objects.create(
            assigned_to=User.objects.get(id=data.get("assigned_to"))
            if data.get("assigned_to")
            else None,
            title=data["task_title"],
            priority=data.get("task_priority", "medium"),
            due_date=parse_datetime(data["due_date"]),
            notes=data.get("notes", ""),
            amount=data.get("amount", 0),
            lead=Lead.objects.get(id=data["lead_id"]) if data.get("lead_id") else None,
        )

        # Создаем связанные Deal
        deals_data = data.get("deals", [])
        for deal in deals_data:
            Deal.objects.create(
                title=deal["title"],
                expected_close_date=deal.get("expected_close_date"),
                task=task,
            )

        return JsonResponse({"status": "success", "task_id": task.id})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@require_POST  # можно использовать @require_http_methods(["POST", "DELETE"]) если хотите
def delete_task(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        task.delete()
        return JsonResponse({"status": "success"})
    except Task.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Задача не найдена"}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
def delete_document(request, pk):
    try:
        doc = Leaddocement.objects.get(pk=pk)
        doc.delete()
        return JsonResponse({"success": True})
    except Leaddocement.DoesNotExist:
        return JsonResponse({"success": False, "error": "Документ не найден"})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def save_task(request, task_id):
    if request.method == "GET":
        try:
            task = (
                Task.objects.select_related("lead", "assigned_to")
                .prefetch_related("deal_set")
                .get(id=task_id)
            )

            data = {
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "due_date": task.due_date.strftime("%Y-%m-%dT%H:%M")
                if task.due_date
                else "",
                "amount": float(task.amount or 0),
                "notes": task.notes,
                "assigned_to": task.assigned_to.id if task.assigned_to else None,
                "lead_id": task.lead.id if task.lead else None,
                "deals": [
                    {
                        "id": deal.id,
                        "title": deal.title,
                        "expected_close_date": deal.expected_close_date.strftime(
                            "%Y-%m-%d"
                        )
                        if deal.expected_close_date
                        else "",
                        "stage": deal.stage,
                    }
                    for deal in task.deal_set.all()
                ],
            }
            return JsonResponse({"status": "success", "task": data})
        except Task.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Задача не найдена"}, status=404
            )

    elif request.method == "POST":
        try:
            data = json.loads(request.body)

            task = Task.objects.get(id=task_id)
            task.title = data.get("task_title", task.title)
            task.priority = data.get("task_priority", task.priority)
            task.due_date = parse_datetime(data.get("due_date")) or task.due_date
            task.notes = data.get("notes", task.notes)
            task.amount = data.get("amount", task.amount)

            assigned_to_id = data.get("assigned_to")
            if assigned_to_id:
                task.assigned_to = User.objects.get(id=assigned_to_id)
            else:
                task.assigned_to = None

            lead_id = data.get("lead_id")
            if lead_id:
                task.lead = Lead.objects.get(id=lead_id)
            else:
                task.lead = None

            task.save()

            deals_data = data.get("deals", [])
            sent_deal_ids = []

            for deal_data in deals_data:
                deal_id = deal_data.get("id")
                title = deal_data.get("title", "").strip()
                expected_close_date_str = deal_data.get("expected_close_date")
                expected_close_date = None
                if expected_close_date_str:
                    try:
                        expected_close_date = datetime.strptime(
                            expected_close_date_str, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        expected_close_date = None

                if deal_id:
                    try:
                        deal = Deal.objects.get(id=deal_id, task=task)
                        current_stage = deal.stage  # сохраняем текущий stage
                        deal.title = title
                        deal.expected_close_date = expected_close_date
                        deal.stage = current_stage  # явно оставляем старый stage
                        deal.save()
                        sent_deal_ids.append(deal.id)
                    except Deal.DoesNotExist:
                        new_deal = Deal.objects.create(
                            title=title,
                            expected_close_date=expected_close_date,
                            task=task,
                        )
                        sent_deal_ids.append(new_deal.id)
                else:
                    new_deal = Deal.objects.create(
                        title=title, expected_close_date=expected_close_date, task=task
                    )
                    sent_deal_ids.append(new_deal.id)

            # Удаляем сделки, которые не пришли в обновлении
            task.deal_set.exclude(id__in=sent_deal_ids).delete()

            return JsonResponse({"status": "success", "task_id": task.id})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
def toggle_deal_stage(request):
    deal_id = request.POST.get("deal_id")

    if not deal_id:
        return JsonResponse({"success": False, "error": "ID сделки не передан"})

    try:
        deal = Deal.objects.get(id=deal_id)
    except Deal.DoesNotExist:
        return JsonResponse({"success": False, "error": "Сделка не найдена"})

    # Логика смены этапа
    if deal.stage == "won":
        deal.stage = "lost"
    else:
        deal.stage = "won"

    deal.save()

    return JsonResponse({"success": True, "new_stage": deal.stage})


@require_POST
def get_task_payment(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({"success": False, "error": "Задача не найдена"})

    if task.payment:
        return JsonResponse({"success": False, "error": "Платеж уже создан"})

    # Создаем новый платеж
    payment = StatusPayment.objects.create(
        amount=task.amount, description=f"Платеж по задаче #{task.id}", status="payout"
    )

    # Связываем с задачей
    task.payment = payment
    task.save()

    return JsonResponse({"success": True, "payment_id": payment.id})


@method_decorator(csrf_exempt, name="dispatch")
class TaskCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = request.POST

        title = data.get("title")
        assigned_to_id = data.get("assigned_to")
        priority = data.get("priority", "medium")
        due_date = data.get("due_date")
        notes = data.get("notes", "")
        lead_id = data.get("lead")

        if not title or not due_date:
            return JsonResponse(
                {"success": False, "error": "Заголовок и срок обязательны"}, status=400
            )

        try:
            task = Task.objects.create(
                title=title,
                assigned_to=Profile.objects.get(id=assigned_to_id)
                if assigned_to_id
                else None,
                priority=priority,
                due_date=due_date,
                notes=notes,
                lead=Lead.objects.get(id=lead_id) if lead_id else None,
                type="at_work",  # тип по умолчанию
            )
            return JsonResponse({"success": True, "task_id": task.id})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@require_POST
@login_required
def create_note(request):
    content = request.POST.get("content", "").strip()
    task_id = request.POST.get("task")

    if not content:
        return JsonResponse({"success": False, "error": "Текст обязателен"})

    note = Note(content=content, author=request.user)

    if task_id:
        try:
            note.task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return JsonResponse({"success": False, "error": "Задача не найдена"})

    note.save()
    return JsonResponse({"success": True, "note_id": note.id})


class LeadTasksPartialView(View):
    def get(self, request, pk):
        # Пагинация
        lead = get_object_or_404(Lead, pk=pk)
        tasks = Task.objects.filter(lead=lead)

        # Получаем текущую страницу
        page_number = request.GET.get("page", 1)
        paginator = Paginator(tasks, 6)  # 10 сделок на странице
        page_obj = paginator.get_page(page_number)

        # Рендерим только сделки для текущей страницы
        html = render_to_string(
            "moderations/leads/_tasks_list.html", {"tasks": page_obj}
        )

        # Передаем, есть ли еще страницы для загрузки
        has_next = page_obj.has_next()
        return JsonResponse(
            {
                "html": html,
                "has_next": has_next,
                "next_page": page_obj.next_page_number() if has_next else None,
            }
        )


class LeadDocumentUploadView(View):
    def post(self, request, *args, **kwargs):
        lead_id = request.POST.get("lead_id")
        title = request.POST.get("title")
        file = request.FILES.get("file")

        if not (lead_id and title and file):
            return JsonResponse({"error": "Данные неполные"}, status=400)

        try:
            lead = Lead.objects.get(id=lead_id)
        except Lead.DoesNotExist:
            return JsonResponse({"error": "Лид не найден"}, status=404)

        doc = Leaddocement.objects.create(
            user=request.user, title=title, lead=lead, file=file
        )
        return JsonResponse(
            {
                "message": "Файл успешно загружен",
                "doc_id": doc.id,
                "title": doc.title,
                "file_url": doc.file.url,
                "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M"),
                "username": request.user.username,
            }
        )


def load_task_notes(request, task_id):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        task = get_object_or_404(Task, id=task_id)
        notes = task.note_set.select_related("author").all()
        html = render(
            request, "moderations/leads/task_notes.html", {"notes": notes}
        ).content.decode("utf-8")
        return JsonResponse({"html": html})
    return JsonResponse({"error": "Invalid request"}, status=400)


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    model = Lead
    template_name = "moderations/leads/lead_confirm_delete.html"
    success_url = reverse_lazy("crm:leadlist")
