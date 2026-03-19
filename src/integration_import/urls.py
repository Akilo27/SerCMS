from django.urls import path
from . import views

app_name = "import"


urlpatterns = [
    path("upload-csv/", views.UploadCSVView.as_view(), name="upload_csv"),
    path(
        "upload-from-disk/",
        views.UploadFromDiskCSVView.as_view(),
        name="upload_from_disk",
    ),
    path("download/<int:upload_id>/", views.manual_download, name="manual_download"),
]
