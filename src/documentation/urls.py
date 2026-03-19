from django.urls import path

app_name = "documentation"
from . import views


urlpatterns = [
    path(
        "profile/documentation/",
        views.DocumentationsListView.as_view(),
        name="documentations_profile",
    ),
]
