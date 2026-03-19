from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from integration_import.models import ImportCsv, ImportCsvElement
from .tasks import start_of_processing_csv
import os
import shutil
from django.conf import settings


@receiver(post_save, sender=ImportCsv)
def signal_of_processing_csv(sender, instance, created, **kwargs):
    if not created:
        return
    csv_file = instance.file
    if not csv_file:
        return

    start_of_processing_csv.delay(instance.id)


@receiver(post_delete, sender=ImportCsvElement)
def delete_import_element_directory(sender, instance, **kwargs):
    if not instance.import_csv.elements.exists():
        directory = os.path.join(
            settings.MEDIA_ROOT, "import_elements", str(instance.import_csv.id)
        )
        if os.path.isdir(directory):
            shutil.rmtree(directory)
