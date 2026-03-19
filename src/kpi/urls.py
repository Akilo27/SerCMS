from django.urls import path
from . import views

app_name = "kpi"

urlpatterns = [
    path('employee/<int:pk>/kpi/', views.EmployeeKPIDetailView.as_view(), name='employee_kpi_detail'),
    path('monthly-kpi/toggle/<int:pk>/', views.toggle_kpi_status, name='toggle_kpi_status'),

    # Department URLs
    path('moderation/employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('moderation/employees/create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('moderation/employees/<int:pk>/update/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('moderation/employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),

    path('moderation/departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('moderation/departments/new/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('moderation/departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('moderation/departments/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),

    # Change URLs
    path('moderation/changes/', views.ChangeListView.as_view(), name='change_list'),
    path('moderation/changes/new/', views.ChangeCreateView.as_view(), name='change_create'),
    path('moderation/changes/<int:pk>/edit/', views.ChangeUpdateView.as_view(), name='change_update'),
    path('moderation/changes/<int:pk>/delete/', views.ChangeDeleteView.as_view(), name='change_delete'),

    path('moderation/employee-positions/', views.EmployeePositionListView.as_view(), name='employee_positions_list'),
    path('moderation/employee-positions/new/', views.EmployeePositionCreateView.as_view(), name='employee_positions_create'),
    path('moderation/employee-positions/<int:pk>/edit/', views.EmployeePositionUpdateView.as_view(), name='employee_positions_update'),
    path('moderation/employee-positions/<int:pk>/delete/', views.EmployeePositionDeleteView.as_view(), name='employee_positions_delete'),
    path('ajax/create-bonus/', views.create_bonus_ajax, name='create_bonus_ajax'),
    path('ajax/create-prize/', views.create_prize_ajax, name='create_prize_ajax'),
    path('ajax/create-penalty/', views.create_penalty_ajax, name='create_penalty_ajax'),

]