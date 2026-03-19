from django.views.generic import ListView
from .models import Documentations


class DocumentationsListView(ListView):
    model = Documentations
    template_name = "site/documentations.html"
    context_object_name = "documentations"
    paginate_by = 1

    def get_queryset(self):
        user_type = self.request.user.type
        return Documentations.objects.filter(type=user_type)
