from django.urls import path
from . import views

app_name = "delivery"


urlpatterns = [
    path("check-courier/", views.check_courier, name="check-courier"),
]
