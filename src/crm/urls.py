from django.urls import path

app_name = "crm"
from . import views


urlpatterns = [
    path("my-tasks/", views.UserTaskListView.as_view(), name="my_tasks"),
    path("", views.LeadListView.as_view(), name="leadlist"),
    path(
        "lead/new/", views.LeadCreateRedirectView.as_view(), name="lead_create_redirect"
    ),
    path("lead/<int:pk>/edit/", views.LeadUpdateView.as_view(), name="lead_update"),
    path("<int:pk>/update/", views.LeadUpdateView.as_view(), name="update"),
    path(
        "ajax/create-payment/",
        views.CreateStatusPaymentAjaxView.as_view(),
        name="ajax_create_payment",
    ),
    path(
        "ajax/create-task-and-deals/",
        views.create_task_and_deals,
        name="create_task_and_deals",
    ),
    path("get-task/<int:task_id>/", views.save_task, name="get_task_data"),
    path("delete_task/<int:task_id>/", views.delete_task, name="delete_task"),
    path("delete-document/<int:pk>/", views.delete_document, name="delete_document"),
    path("toggle-deal-stage/", views.toggle_deal_stage, name="toggle_deal_stage"),
    path(
        "get-task-payment/<int:task_id>/",
        views.get_task_payment,
        name="get_task_payment",
    ),
    path(
        "<int:pk>/lead-document/",
        views.LeadDocumentView.as_view(),
        name="lead_document",
    ),
    path("<int:pk>/lead-task/", views.LeadTaskView.as_view(), name="lead_task"),
    path("<int:pk>/delete/", views.LeadDeleteView.as_view(), name="delete"),
    path(
        "upload-lead-document/",
        views.LeadDocumentUploadView.as_view(),
        name="upload_lead_document",
    ),
    path(
        "leads/<int:pk>/tasks/",
        views.LeadTasksPartialView.as_view(),
        name="lead_tasks_partial",
    ),
    path(
        "load-task-notes/<int:task_id>/", views.load_task_notes, name="load_task_notes"
    ),
    path("tasks/create/", views.TaskCreateView.as_view(), name="task_create"),
    path("notes/create/", views.create_note, name="create_note"),
    path(
        "leads/update_status/<int:pk>/",
        views.update_lead_status,
        name="update_lead_status",
    ),
    path(
        "leads/delete/<int:pk>/",
        views.delete_single_lead_ajax,
        name="delete_single_lead_ajax",
    ),
    path("tasks/update-status/", views.update_task_status, name="update_task_status"),
    path('update-task-position/', views.update_task_position, name='update_task_position'),
    path('update-deal-position/', views.update_deal_position, name='update_deal_position'),
    path('add_subdeal/', views.add_subdeal, name='add_subdeal'),

]
