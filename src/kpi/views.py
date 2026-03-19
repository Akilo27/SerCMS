from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.utils import timezone

from .forms import EmployeePositionForm
from .models import Department, Change, EmployeePosition, Bonus, Prize, Penalty, Employee, MonthlyKPI
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

User = get_user_model()


class EmployeeKPIDetailView(DetailView):
    model = Employee
    template_name = 'moderations/employee_kpi_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.get_object()
        current_month = str(timezone.now().month)

        context['kpis'] = MonthlyKPI.objects.filter(
            employee=employee,
            month=current_month
        ).select_related('bonus', 'prize', 'penalty')

        context['current_month'] = dict(MonthlyKPI.MONTH_CHOICES).get(current_month)
        context['current_year'] = timezone.now().year
        return context


def toggle_kpi_status(request, pk):
    if request.method == 'POST' and request.is_ajax():
        kpi = get_object_or_404(MonthlyKPI, pk=pk)
        kpi.completed = not kpi.completed
        if kpi.completed:
            kpi.completion_date = timezone.now().date()
        else:
            kpi.completion_date = None
        kpi.save()
        return JsonResponse({
            'status': 'success',
            'completed': kpi.completed,
            'completion_date': kpi.completion_date.strftime('%d.%m.%Y') if kpi.completion_date else None
        })
    return JsonResponse({'status': 'error'}, status=400)


class EmployeeListView(ListView):
    model = Employee
    template_name = 'moderations/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'user', 'department', 'position'
        )
        # Добавьте здесь любую дополнительную фильтрацию, если нужно
        return queryset

class EmployeeCreateView(CreateView):
    model = Employee
    template_name = 'moderations/employee_form.html'
    fields = ['user', 'department', 'position']
    success_url = reverse_lazy('kpi:employee_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Оптимизация queryset'ов для полей ForeignKey
        form.fields['user'].queryset = User.objects.filter(employee_profile__isnull=True)
        form.fields['department'].queryset = Department.objects.all()
        form.fields['position'].queryset = EmployeePosition.objects.all()
        return form

class EmployeeUpdateView(UpdateView):
    model = Employee
    template_name = 'moderations/employee_form.html'
    fields = ['department', 'position']
    success_url = reverse_lazy('kpi:employee_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Оптимизация queryset'ов для полей ForeignKey
        form.fields['department'].queryset = Department.objects.all()
        form.fields['position'].queryset = EmployeePosition.objects.all()
        return form

class EmployeeDeleteView(DeleteView):
    model = Employee
    template_name = 'moderations/employee_confirm_delete.html'
    success_url = reverse_lazy('kpi:employee_list')


@csrf_exempt
@require_POST
def create_bonus_ajax(request):
    try:
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason', '')

        bonus = Bonus.objects.create(
            Name=name,
            amount=amount,
            reason=reason
        )
        return JsonResponse({
            'success': True,
            'id': bonus.CustomerID,
            'text': str(bonus)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_POST
def create_prize_ajax(request):
    try:
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason', '')

        prize = Prize.objects.create(
            Name=name,
            amount=amount,
            reason=reason
        )
        return JsonResponse({
            'success': True,
            'id': prize.CustomerID,
            'text': str(prize)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_POST
def create_penalty_ajax(request):
    try:
        name = request.POST.get('name')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason', '')

        penalty = Penalty.objects.create(
            Name=name,
            amount=amount,
            reason=reason
        )
        return JsonResponse({
            'success': True,
            'id': penalty.CustomerID,
            'text': str(penalty)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

# Department Views
@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class DepartmentListView(ListView):
    model = Department
    template_name = 'moderations/department_list.html'
    context_object_name = 'departments'
    paginate_by = 10

    def get_queryset(self):
        return Department.objects.all().order_by('Name')


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    template_name = 'moderations/department_form.html'
    fields = ['Name', 'Description', 'Guide', 'Staff', 'Chart']
    success_url = reverse_lazy('kpi:department_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['Guide'].queryset = self.request.user.__class__.objects.filter(is_staff=True)
        return form


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    template_name = 'moderations/department_form.html'
    fields = ['Name', 'Description', 'Guide', 'Staff', 'Chart']
    success_url = reverse_lazy('kpi:department_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['Guide'].queryset = self.request.user.__class__.objects.filter(is_staff=True)
        return form


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Department
    template_name = 'moderations/department_confirm_delete.html'
    success_url = reverse_lazy('kpi:department_list')


# Change Views
class ChangeListView(LoginRequiredMixin, ListView):
    model = Change
    template_name = 'moderations/change_list.html'
    context_object_name = 'changes'
    paginate_by = 10

    def get_queryset(self):
        return Change.objects.all().order_by('Name')


class ChangeCreateView(LoginRequiredMixin, CreateView):
    model = Change
    template_name = 'moderations/change_form.html'
    fields = ['Name', 'Schedule']
    success_url = reverse_lazy('kpi:change_list')


class ChangeUpdateView(LoginRequiredMixin, UpdateView):
    model = Change
    template_name = 'moderations/change_form.html'
    fields = ['Name', 'Schedule']
    success_url = reverse_lazy('kpi:change_list')


class ChangeDeleteView(LoginRequiredMixin, DeleteView):
    model = Change
    template_name = 'moderations/change_confirm_delete.html'
    success_url = reverse_lazy('kpi:change_list')


class EmployeePositionListView(LoginRequiredMixin, ListView):
    model = EmployeePosition
    template_name = 'moderations/employee_positions_list.html'
    context_object_name = 'positions'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')

        if search_query:
            queryset = queryset.filter(
                Q(Name__icontains=search_query) |
                Q(Description__icontains=search_query)
            )
        return queryset.order_by('Name')


class EmployeePositionCreateView(LoginRequiredMixin, CreateView):
    model = EmployeePosition
    form_class = EmployeePositionForm
    template_name = 'moderations/employee_positions_form.html'
    success_url = reverse_lazy('kpi:employee_positions_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['Change'].queryset = Change.objects.all().order_by('Name')
        return form

class EmployeePositionUpdateView(LoginRequiredMixin, UpdateView):
    model = EmployeePosition
    form_class = EmployeePositionForm
    template_name = 'moderations/employee_positions_form.html'
    success_url = reverse_lazy('kpi:employee_positions_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['Change'].queryset = Change.objects.all().order_by('Name')
        return form

class EmployeePositionDeleteView(LoginRequiredMixin, DeleteView):
    model = EmployeePosition
    template_name = 'moderations/employee_positions_delete.html'
    success_url = reverse_lazy('kpi:employee_positions_list')
