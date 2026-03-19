from django.urls import path

app_name = "hr"
from . import views


urlpatterns = [
    path("vacancy/", views.VacancyView.as_view(), name="vacancys"),
    path(
        "vacancy/<slug:slug>/", views.VacancyDetailView.as_view(), name="vacancydetail"
    ),
]
