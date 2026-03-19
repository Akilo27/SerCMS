from django.urls import path

app_name = "useraccount"
from . import views

urlpatterns = [
    path("dashboard/", views.StatisticView.as_view(), name="statistic"),
    path("edit_profile/", views.EditMyProfileView.as_view(), name="edit_profile"),
    path("notification/", views.NotificationView.as_view(), name="notification"),
    # Брони
    # Тикеты
    path("tickets/", views.TicketsView.as_view(), name="tickets"),
    path("tickets/create/", views.TicketCreateView.as_view(), name="ticket_create"),
    path("tickets/delete/", views.TicketDeleteView.as_view(), name="ticket_delete"),
    path(
        "tickets/<uuid:ticket_id>/add_comment/",
        views.TicketCommentCreateView.as_view(),
        name="add_comment",
    ),
    path(
        "tickets/<slug:pk>/", views.TicketMessageView.as_view(), name="ticket_message"
    ),
    # Вылпаты
    path("withdrawpoint/", views.WithdrawPagePoint.as_view(), name="withdraw_point"),
    path("referrals/", views.ReferralListView.as_view(), name="referrals_list"),
    path("withdraw/", views.WithdrawPage.as_view(), name="withdraw"),
    path(
        "withdraw/create/", views.WithdrawCreateView.as_view(), name="withdraw_create"
    ),
    path("company/", views.CompanyView.as_view(), name="company"),
    path("groups/", views.PersonalGroupListView.as_view(), name="groups_list"),
    path(
        "groups/create/", views.PersonalGroupCreateView.as_view(), name="groups_create"
    ),
    path(
        "groups/<uuid:pk>/update/",
        views.PersonalGroupUpdateView.as_view(),
        name="groups_update",
    ),
    path(
        "groups/<uuid:pk>/ajax-delete/",
        views.PersonalGroupAjaxDeleteView.as_view(),
        name="ajax_group_delete",
    ),
    # Карта
    path("card/create/", views.CardsCreateView.as_view(), name="cards_create"),
    path("card/update/<int:pk>/", views.CardsUpdateView.as_view(), name="cards_update"),
]
