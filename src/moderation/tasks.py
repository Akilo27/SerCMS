from celery import shared_task
from shop.models import ImportHistory
from .services import FileImporter

@shared_task
def import_file_task(import_history_id):
    import_history = ImportHistory.objects.get(id=import_history_id)
    importer = FileImporter(import_history)
    importer.import_data()
