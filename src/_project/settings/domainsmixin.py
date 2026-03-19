from django.shortcuts import redirect
from django.contrib.sites.models import Site
from webmain.models import ExtendedSite


class DomainTemplateMixin:
    def dispatch(self, request, *args, **kwargs):
        current_domain = request.get_host()

        try:
            site = Site.objects.get(domain=current_domain)
            _ = site.extended  # Проверка, что есть ExtendedSite
        except (Site.DoesNotExist, ExtendedSite.DoesNotExist, AttributeError):
            # Если домен не зарегистрирован или не привязан ExtendedSite — редирект
            return redirect("webmain:development")

        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        current_domain = self.request.get_host()
        site = Site.objects.get(domain=current_domain)
        template_folder = f"site/{site.extended.templates}/"
        final_template = f"{template_folder}{self.template_name}"
        return [final_template]
