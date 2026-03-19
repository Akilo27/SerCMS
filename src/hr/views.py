from django.shortcuts import render
from _project.domainsmixin import DomainTemplateMixin
from django.views.generic import ListView, DetailView
from hr.models import Vacancy
from django.contrib.sites.models import Site
from django.http import JsonResponse
from django.core.paginator import Paginator
from .forms import VacancyResponseForm
from webmain.models import Seo
from django.shortcuts import get_object_or_404


# Create your views here.
class VacancyView(DomainTemplateMixin, ListView):
    model = Vacancy
    context_object_name = "vacancies"
    paginate_by = 10
    template_name = "vacancys.html"

    def get_queryset(self):
        current_domain = self.request.get_host()
        queryset = Vacancy.objects.filter(site__domain=current_domain, is_active=True)

        # Поиск по названию
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        # Фильтр по зарплате
        salary_min = self.request.GET.get("salary_min")
        salary_max = self.request.GET.get("salary_max")
        if salary_min:
            queryset = queryset.filter(salary__gte=salary_min)
        if salary_max:
            queryset = queryset.filter(salary__lte=salary_max)

        # Фильтр по типу работы
        work_schedule = self.request.GET.get("work_schedule")
        if work_schedule:
            queryset = queryset.filter(work_schedule=work_schedule)

        return queryset.order_by("-posted_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["site"] = Site.objects.filter(domain=self.request.get_host()).first()
        current_site = get_object_or_404(Site, domain=self.request.get_host())

        seo_data = Seo.objects.filter(site=current_site, pagetype=19).first()

        if seo_data:
            context["seo_previev"] = seo_data.previev
            context["seo_title"] = seo_data.title
            context["seo_description"] = seo_data.metadescription
            context["seo_propertytitle"] = seo_data.propertytitle
            context["seo_propertydescription"] = seo_data.propertydescription
        else:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None
        return context

    def get(self, request, *args, **kwargs):
        self.template_name = self.get_template_names()[0]
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        self.object_list = page_obj.object_list

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            vacancies_data = [
                {
                    "title": vacancy.title,
                    "description": vacancy.description,
                    "requirements": vacancy.requirements,
                    "salary": str(vacancy.salary) if vacancy.salary else "Не указано",
                    "location": vacancy.location or "Не указано",
                    "posted_at": vacancy.posted_at.strftime("%Y-%m-%d"),
                    "image": vacancy.image.url if vacancy.image else None,
                    "slug": vacancy.slug,
                    "url": f"/vacancy/{vacancy.slug}/",
                }
                for vacancy in page_obj.object_list
            ]
            return JsonResponse(
                {"vacancies": vacancies_data, "has_next": page_obj.has_next()}
            )

        context = self.get_context_data()
        context["page_obj"] = page_obj
        return render(request, self.template_name, context)


class VacancyDetailView(DomainTemplateMixin, DetailView):
    """Страницы"""

    model = Vacancy
    template_name = "vacancy_detail.html"
    context_object_name = "vacancy"
    slug_field = "slug"

    def get_queryset(self):
        # Filter the queryset for the "blog" view based on the current domain
        current_domain = self.request.get_host()
        # Add your domain-specific logic here to filter Blogs queryset
        filtered_page = Vacancy.objects.filter(site__domain=current_domain)
        return filtered_page

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VacancyResponseForm(request.POST, request.FILES)
        if form.is_valid():
            response = form.save(commit=False)
            response.vacancy = self.object
            response.save()
            return JsonResponse({"success": True, "message": "Отклик отправлен!"})
        return JsonResponse({"success": False, "errors": form.errors}, status=400)
