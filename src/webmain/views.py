import itertools

from django.http import HttpResponseRedirect, JsonResponse, HttpResponseServerError
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    TemplateView,
    CreateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q, functions as F
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import Site

from webmain.forms import SubscriptionForm, CommentForm, CooperationForm
from webmain.models import (
    Faqs,
    ContactPage,
    TagsBlogs,
    AboutPage,
    HomePage,
    Seo,
    Pages,
    CategorysBlogs,
    Blogs,
    Sponsorship,
    Gallery,
    Service,
    Price,
    Comments,
)
import logging
import json
from django.utils.timezone import localtime
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth import views as auth_views
from useraccount.forms import (
    SignUpForm,
    PasswordResetEmailForm,
    SetPasswordFormCustom,
    CustomAuthenticationForm,
)
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordResetDoneView,
)
from shop.models import Products, Manufacturers, Brands, ProductsVariable, Categories, Tag
from _project.domainsmixin import DomainTemplateMixin

from shop.models import Cart
from useraccount.models import SearchQuery, Profile
from useraccount.utils import ensure_session_key
from django.utils.timezone import now
from django.views.decorators.http import require_GET, require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.html import strip_tags

from shop.models import Reviews, FaqsProducts


class HomePageView(TemplateView):
    template_name = "_development.html"


logger = logging.getLogger(__name__)

# Настройки
SUGGESTION_LIMIT_PER_TYPE = 5   # лимит на каждый тип сущности
HISTORY_LIMIT = 8               # сколько элементов истории возвращать
TOTAL_SUGGESTIONS_CAP = 25      # общий потолок подсказок


# --- Вспомогательные функции -------------------------------------------------
def _log_search(request, q: str) -> None:
    """Логирование поискового запроса в SearchQuery по user или session_key."""
    q = (q or "").strip()
    if not q:
        return

    session_key = ensure_session_key(request)
    if request.user.is_authenticated:
        obj, _ = SearchQuery.objects.get_or_create(
            user=request.user, query=q, defaults={"session_key": ""}
        )
    else:
        obj, _ = SearchQuery.objects.get_or_create(
            session_key=session_key, query=q, defaults={"user": None}
        )

    obj.count += 1
    obj.last_searched = now()
    obj.save(update_fields=["count", "last_searched"])


def _safe_reverse(name: str, **kwargs) -> str | None:
    """Пробуем reverse(name, kwargs). Если урла с таким name нет — вернем None."""
    try:
        return reverse(name, kwargs=kwargs)
    except Exception:
        return None


def _model_has_field(model, field_name: str) -> bool:
    return any(f.name == field_name for f in model._meta.fields)



@require_GET
def search_suggest(request):
    """
    GET /search/suggest/?q=...
    Ищем по: Brands, Manufacturers, Categories, Products, ProductsVariable.
    Если q пусто — отдаём только историю.
    """
    q = (request.GET.get("q") or "").strip()
    session_key = ensure_session_key(request)

    # История
    if request.user.is_authenticated:
        history_qs = SearchQuery.objects.filter(user=request.user)
    else:
        history_qs = SearchQuery.objects.filter(
            session_key=session_key, user__isnull=True
        )

    history = list(
        history_qs.order_by("-last_searched")
        .values_list("query", flat=True)[:HISTORY_LIMIT]
    )

    suggestions: list[dict] = []

    if q:
        # --- Brands ---
        brands = (
            Brands.objects.filter(Q(name__icontains=q) | Q(slug__icontains=q))
            .values("id", "name", "slug")[:SUGGESTION_LIMIT_PER_TYPE]
        )
        for b in brands:
            url = _safe_reverse("shop:brand_detail", slug=b["slug"]) or f"/ru/brand/{b['slug']}/"
            suggestions.append({
                "type": "brand",
                "title": b["name"],
                "subtitle": "Бренд",
                "url": url,
                "id": b["id"],
            })

        # --- Manufacturers ---
        mans = (
            Manufacturers.objects.filter(Q(name__icontains=q) | Q(slug__icontains=q))
            .values("id", "name", "slug")[:SUGGESTION_LIMIT_PER_TYPE]
        )
        for m in mans:
            url = _safe_reverse("shop:manufacturer_detail", slug=m["slug"]) or f"/ru/manufacturer/{m['slug']}/"
            suggestions.append({
                "type": "manufacturer",
                "title": m["name"],
                "subtitle": "Производитель",
                "url": url,
                "id": m["id"],
            })

        # --- Categories ---
        cats = (
            Categories.objects.filter(Q(name__icontains=q) | Q(slug__icontains=q))
            .values("id", "name", "slug")[:SUGGESTION_LIMIT_PER_TYPE]
        )
        for c in cats:
            url = _safe_reverse("shop:category_detail", slug=c["slug"]) or f"/ru/category/{c['slug']}/"
            suggestions.append({
                "type": "category",
                "title": c["name"],
                "subtitle": "Категория",
                "url": url,
                "id": c["id"],
            })

        # --- Products ---
        prods = (
            Products.objects.filter(Q(name__icontains=q) | Q(slug__icontains=q))
            .values("id", "name", "slug")[:SUGGESTION_LIMIT_PER_TYPE]
        )
        for p in prods:
            url = _safe_reverse("shop:product_detail", slug=p["slug"]) or f"/ru/catalog/{p['slug']}/"
            suggestions.append({
                "type": "product",
                "title": p["name"],
                "subtitle": "Товар",
                "url": url,
                "id": p["id"],
            })

        # --- ProductsVariable ---
        vars_q = Q(name__icontains=q) | Q(slug__icontains=q)
        if _model_has_field(ProductsVariable, "sku"):
            vars_q |= Q(sku__icontains=q)
        if _model_has_field(ProductsVariable, "article"):
            vars_q |= Q(article__icontains=q)

        variables = (
            ProductsVariable.objects.filter(vars_q)
            .select_related("products")
            .values("id", "name", "slug", "products__slug", "products__name")
            [:SUGGESTION_LIMIT_PER_TYPE]
        )
        for v in variables:
            product_slug = v.get("products__slug")
            product_name = v.get("products__name") or ""
            if not product_slug:
                continue
            base_url = _safe_reverse("shop:product_detail", slug=product_slug) or f"/ru/product/{product_slug}/"
            suggestions.append({
                "type": "variant",
                "title": v["name"] or f"Вариация {v['id']}",
                "subtitle": ("Вариация • " + product_name).strip(),
                "url": base_url,
                "id": v["id"],
            })

        # Сортировка: товары и вариации выше
        order = {"product": 0, "variant": 1, "category": 2, "brand": 3, "manufacturer": 4}
        suggestions.sort(key=lambda s: (order.get(s["type"], 99), s["title"].lower()))

    return JsonResponse({
        "q": q,
        "suggestions": suggestions[:TOTAL_SUGGESTIONS_CAP],
        "history": history,
    })


@require_POST
def search_log(request):
    q = (request.POST.get("q") or "").strip()
    if not q:
        return HttpResponseBadRequest("Empty query")
    _log_search(request, q)
    return JsonResponse({"ok": True})


@require_POST
def search_history_clear(request):
    session_key = ensure_session_key(request)
    if request.user.is_authenticated:
        SearchQuery.objects.filter(user=request.user).delete()
    else:
        SearchQuery.objects.filter(session_key=session_key, user__isnull=True).delete()
    return JsonResponse({"ok": True})



class HomeView(DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "home.html"
    context_object_name = "homepage"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        homepage = self.get_object()
        context["json_fields"] = {}
        if homepage:
            context["seo_previev"] = homepage.previev
            context["seo_title"] = homepage.title
            context["seo_description"] = homepage.metadescription
            context["seo_propertytitle"] = homepage.propertytitle
            context["seo_propertydescription"] = homepage.propertydescription
        else:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None

        try:
            if homepage.jsontemplate:
                parsed_json = json.loads(homepage.jsontemplate)
                fields = parsed_json[0].get("fields", {})
                context["json_fields"] = fields

                type_to_model = {
                    "services": (Service, "services"),
                    "categorys": (Categories, "categorys"),
                    "blogs": (Blogs, "blogs"),
                    "gallery": (Gallery, "gallery"),
                    "faqs": (Faqs, "faqs"),
                    "sponsorship": (Sponsorship, "sponsorship"),
                    "products": (Products, None),
                    "vendors": (Manufacturers, None),
                }

                for key, value in fields.items():
                    field_type = value.get("type")
                    model_info = type_to_model.get(field_type)
                    if not model_info:
                        continue

                    model_class, default_context_key = model_info

                    ids_raw = value.get("info") or value.get("field") or []
                    # поддержим и строку "1,2,3", и список ["1","2"]
                    if isinstance(ids_raw, str):
                        ids_list = [x.strip() for x in ids_raw.split(",") if x.strip()]
                    elif isinstance(ids_raw, list):
                        ids_list = ids_raw
                    else:
                        ids_list = []

                    # если пришли цифры строками — приведём к int
                    ids_list = [int(x) if isinstance(x, str) and x.isdigit() else x for x in ids_list]

                    qs = model_class.objects.filter(id__in=ids_list)

                    # 1) ключ из JSON (например, category_list)
                    context[key] = qs
                    # 2) при необходимости — ещё и под дефолтным ключом (например, categorys)
                    if default_context_key and key != default_context_key:
                        context[default_context_key] = qs


        except Exception as e:
            print("❌ Ошибка парсинга JSON в HomeView:", e)

        special_offers_qs = Products.objects.filter(stocks=True)[:10]
        # Группируем по 3
        context["special_offers_groups"] = [
            list(group) for group in itertools.zip_longest(*[iter(special_offers_qs)] * 3)
        ]

        new_arrivals_qs = Products.objects.order_by('-create')[:10]
        context["new_arrivals_groups"] = [
            list(group) for group in itertools.zip_longest(*[iter(new_arrivals_qs)] * 3)
        ]

        return context


class AboutView(DomainTemplateMixin, DetailView):
    model = AboutPage
    template_name = "about.html"
    context_object_name = "aboutpage"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(AboutPage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aboutpage = self.get_object()
        if aboutpage:
            context["seo_previev"] = aboutpage.previev
            context["seo_title"] = aboutpage.title
            context["seo_description"] = aboutpage.metadescription
            context["seo_propertytitle"] = aboutpage.propertytitle
            context["seo_propertydescription"] = aboutpage.propertydescription
        else:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None
        # Инициализируем контекст
        context["json_fields"] = {}
        context["services"] = []
        context["blogs"] = []
        context["gallery"] = []
        context["faqs"] = []
        context["sponsorship"] = []
        context["products"] = []

        try:
            if aboutpage.jsontemplate:
                parsed_json = json.loads(aboutpage.jsontemplate)
                fields = parsed_json[0].get("fields", {})
                context["json_fields"] = fields

                # Обрабатываем типы по аналогии
                type_to_model = {
                    "services": (Service, "services"),
                    "blogs": (Blogs, "blogs"),
                    "gallery": (Gallery, "gallery"),
                    "faqs": (Faqs, "faqs"),
                    "sponsorship": (Sponsorship, "sponsorship"),
                    "products": (Products, "products"),
                }

                for key, value in fields.items():
                    field_type = value.get("type")
                    model_info = type_to_model.get(field_type)
                    if model_info:
                        model_class, context_key = model_info
                        ids = value.get("info") or value.get("field") or []
                        if isinstance(ids, list):
                            context[context_key] = model_class.objects.filter(
                                id__in=ids
                            )

        except Exception as e:
            print("❌ Ошибка парсинга JSON в AboutView:", e)

        return context


class ContactView(DomainTemplateMixin, DetailView):
    template_name = "contacts.html"
    context_object_name = "contact"
    model = ContactPage

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(ContactPage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.get_object()
        if contact:
            context["seo_previev"] = contact.previev
            context["seo_title"] = contact.title
            context["seo_description"] = contact.metadescription
            context["seo_propertytitle"] = contact.propertytitle
            context["seo_propertydescription"] = contact.propertydescription
        else:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None
        # Получаем только записи с page_type = 'branches'
        context["branch_contacts"] = contact.contactpageinformation_set.filter(
            page_type="branches"
        )

        context["json_fields"] = {}
        context["services"] = []
        context["blogs"] = []
        context["gallery"] = []
        context["faqs"] = []
        context["sponsorship"] = []
        context["products"] = []

        try:
            if contact.jsontemplate:
                parsed_json = json.loads(contact.jsontemplate)
                fields = parsed_json[0].get("fields", {})
                context["json_fields"] = fields

                type_to_model = {
                    "services": (Service, "services"),
                    "blogs": (Blogs, "blogs"),
                    "gallery": (Gallery, "gallery"),
                    "faqs": (Faqs, "faqs"),
                    "sponsorship": (Sponsorship, "sponsorship"),
                    "products": (Products, "products"),
                }

                for key, value in fields.items():
                    field_type = value.get("type")
                    model_info = type_to_model.get(field_type)
                    if model_info:
                        model_class, context_key = model_info
                        ids = value.get("info") or value.get("field") or []
                        if isinstance(ids, list):
                            context[context_key] = model_class.objects.filter(
                                id__in=ids
                            )

        except Exception as e:
            print("❌ Ошибка парсинга JSON в ContactView:", e)

        return context

    def post(self, request, *args, **kwargs):
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        try:
            Collaborations.objects.create(
                name=name, email=email, subject=subject, phone=phone, message=message
            )
        except:
            pass
        return redirect(reverse("webmain:contacts"))


"""ЧаВо"""


class FaqsView(DomainTemplateMixin, ListView):
    model = Faqs
    template_name = "faqs.html"  # No .html extension
    context_object_name = "faqs"
    paginate_by = 10

    def get_queryset(self):
        # Получаем текущий домен
        current_domain = self.request.get_host()
        # Фильтруем галереи по текущему домену и другим параметрам
        queryset = Faqs.objects.filter(publishet=True, site__domain=current_domain)
        search = self.request.GET.get("search", None)

        if search and search != "None":
            queryset = queryset.filter(Q(name__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=4).first()

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


"""Страницы"""


class PageDetailView(DomainTemplateMixin, DetailView):
    model = Pages
    template_name = "page_detail.html"
    context_object_name = "page"
    slug_field = "slug"

    def get_queryset(self):
        current_domain = self.request.get_host()
        return Pages.objects.filter(site__domain=current_domain)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = CooperationForm()
        contact = self.get_object()

        if contact:
            context["seo_previev"] = contact.previev
            context["seo_title"] = contact.title
            context["seo_description"] = contact.metadescription
            context["seo_propertytitle"] = contact.propertytitle
            context["seo_propertydescription"] = contact.propertydescription
        else:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CooperationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                self.request.path
            )  # Перезагружаем ту же страницу
        context = self.get_context_data(object=self.object)
        context["form"] = form  # Передаём форму с ошибками
        return self.render_to_response(context)


"""Новости"""


class BlogView(DomainTemplateMixin, ListView):
    model = Blogs
    context_object_name = "blogs"
    paginate_by = 10
    template_name = "blogs.html"

    def get_queryset(self):
        # Получаем домен текущего сайта
        current_domain = self.request.get_host()
        # Основной запрос к блогам
        blogs = Blogs.objects.filter(site__domain=current_domain).order_by("-create")

        # Фильтрация по категории, поисковому запросу и фильтру
        category_id = self.request.GET.get("category", None)
        filter_type = self.request.GET.get("filter", None)
        search = self.request.GET.get("search", None)

        if category_id:
            blogs = blogs.filter(category__id=category_id)

        if search and search != "None":  # Игнорировать 'None' как значение
            blogs = blogs.filter(name__icontains=search)

        if filter_type:
            if filter_type == "1":
                blogs = blogs.order_by("name")
            elif filter_type == "2":
                blogs = blogs.order_by("-create")
            elif filter_type == "3":
                blogs = blogs.order_by("create")

        return blogs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_domain = self.request.get_host()
        current_site = Site.objects.filter(domain=current_domain).first()

        context["selected_category"] = self.request.GET.get("category")
        context["selected_tag"] = self.request.GET.get("tag")
        context["search_query"] = self.request.GET.get("search", "")

        # Категории и теги с учётом сайта
        context["categorysblogs"] = CategorysBlogs.objects.filter(
            publishet=True, site=current_site
        )
        context["tags"] = TagsBlogs.objects.filter(publishet=True, site=current_site)
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=1).first()

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
            blogs_data = []
            for blog in page_obj.object_list:
                # чистим описание от html
                clean_descr = strip_tags(blog.description or "")
                # ограничиваем по длине
                short_descr = (clean_descr[:150] + "…") if len(clean_descr) > 150 else clean_descr

                blogs_data.append({
                    "name": blog.name,
                    "description": short_descr,
                    "author": blog.author.username if blog.author else "Администрация",
                    "create": blog.create.strftime("%Y-%m-%d"),
                    "url": blog.get_absolute_url(),
                    "image": blog.image.url if blog.image else None,
                })

            return JsonResponse({"blogs": blogs_data, "has_next": page_obj.has_next()})

        if not self.template_name:
            raise ValueError("template_name не определен!")

        context = self.get_context_data()
        context["blogs"] = page_obj
        return render(request, self.template_name, context)


class BlogDetailView(DomainTemplateMixin, DetailView):
    """Страницы"""

    model = Blogs
    template_name = "blog_detail.html"
    context_object_name = "blog"
    slug_field = "slug"

    def get_queryset(self):
        # Filter the queryset for the "blog" view based on the current domain
        current_domain = self.request.get_host()
        return Blogs.objects.filter(site__domain=current_domain)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blog = context["blog"]
        current_domain = self.request.get_host()

        # Get settings
        settings = HomePage.objects.filter(site__domain=current_domain).first()

        # Get two latest news (excluding the current blog)
        latest_news = Blogs.objects.filter(
            site__domain=current_domain
        ).exclude(
            id=blog.id
        ).order_by('-create')[:2]  # Assuming you have a 'create' field

        # SEO and page information
        if blog:
            context.update({
                "pageinformation": blog.description,
                "seo_previev": blog.previev,
                "seo_title": blog.title,
                "seo_description": blog.metadescription,
                "seo_propertytitle": blog.propertytitle,
                "seo_propertydescription": blog.propertydescription,
                "latest_news": latest_news,  # Add the two latest news to context
            })
        else:
            context.update({
                "pageinformation": None,
                "seo_previev": None,
                "seo_title": None,
                "seo_description": None,
                "seo_propertytitle": None,
                "seo_propertydescription": None,
                "latest_news": None,
            })

        return context


class BlogCommentsView(View):
    def get(self, request, slug):
        try:
            blog = Blogs.objects.get(slug=slug)
        except Blogs.DoesNotExist:
            return JsonResponse({"error": "Blog not found"}, status=404)

        content_type = ContentType.objects.get_for_model(Blogs)

        limit = int(request.GET.get("limit", 5))  # Количество комментариев за раз
        offset = int(request.GET.get("offset", 0))  # Смещение

        comments_qs = Comments.objects.filter(
            content_type=content_type, object_id=str(blog.id), publishet=True
        ).order_by("-create")

        total_comments = comments_qs.count()  # Общее количество комментариев
        comments = comments_qs[offset : offset + limit]  # Берем нужное количество

        data = {
            "comments": [
                {
                    "author": comment.author.get_full_name()
                    if comment.author
                    else f"{comment.first_name} {comment.last_name}",
                    "date": localtime(comment.create).strftime("%b %d, %Y"),
                    "comment": comment.comment,
                    "avatar": comment.author.avatar.url
                    if comment.author and comment.author.avatar
                    else "/static/images/default-avatar.jpg",
                }
                for comment in comments
            ],
            "has_more": offset + limit
            < total_comments,  # Флаг для кнопки "Загрузить ещё"
        }
        return JsonResponse(data)


class AddCommentView(View):
    def post(self, request, slug):
        blog = Blogs.objects.get(slug=slug)
        form = CommentForm(request.POST, user=request.user)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.content_type = ContentType.objects.get_for_model(Blogs)
            comment.object_id = blog.id
            comment.publishet = False  # Ожидает модерации
            comment.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Комментарий отправлен на модерацию!",
                    "author": comment.author.get_full_name()
                    if comment.author
                    else f"{comment.first_name} {comment.last_name}",
                    "date": localtime(comment.create).strftime("%b %d, %Y"),
                    "comment": comment.comment,
                    "avatar": comment.author.avatar.url
                    if comment.author and comment.author.avatar
                    else "/static/images/default-avatar.jpg",
                }
            )

        return JsonResponse({"success": False, "errors": form.errors})


"""Благотворительность"""


class SponsorshipView(DomainTemplateMixin, ListView):
    model = Sponsorship
    template_name = "sponsorship.html"
    context_object_name = "sponsorships"
    paginate_by = 10

    def get_queryset(self):
        # Получаем текущий домен
        current_domain = self.request.get_host()
        # Фильтруем галереи по текущему домену и другим параметрам
        queryset = Sponsorship.objects.filter(
            publishet=True, site__domain=current_domain
        )
        search = self.request.GET.get("search", None)

        if search and search != "None":
            queryset = queryset.filter(Q(name__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_query"] = self.request.GET.get("search", "")
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=13).first()

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
            sponsorship_data = [
                {
                    "name": sponsorship.name,
                    "description": sponsorship.description,
                    "author": sponsorship.author.username
                    if sponsorship.author
                    else "Администрация",
                    "create": sponsorship.create.strftime("%Y-%m-%d"),
                    "url": sponsorship.get_absolute_url(),
                    "image": sponsorship.image.url if sponsorship.image else None,
                }
                for sponsorship in page_obj.object_list
            ]
            return JsonResponse(
                {"sponsorships": sponsorship_data, "has_next": page_obj.has_next()}
            )

        if not self.template_name:
            raise ValueError("template_name не определен!")

        context = self.get_context_data()
        context["sponsorships"] = page_obj  # Данные для обычного рендеринга
        return render(request, self.template_name, context)


class SponsorshipDetailView(DomainTemplateMixin, DetailView):
    """Страница благотворительность"""

    model = Sponsorship
    template_name = "sponsorship_detail.html"
    context_object_name = "sponsorship"
    slug_field = "slug"

    def get_queryset(self):
        return Sponsorship.objects.filter(publishet=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["blog"] = Blogs.objects.all().filter(publishet=True)
        sponsorship = context["sponsorship"]
        if sponsorship:
            context["pageinformation"] = sponsorship.description
            context["seo_previev"] = sponsorship.previev
            context["seo_title"] = sponsorship.title
            context["seo_description"] = sponsorship.metadescription
            context["seo_propertytitle"] = sponsorship.propertytitle
            context["seo_propertydescription"] = sponsorship.propertydescription
        else:
            context["pageinformation"] = None
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None
        return context


"""Галерея"""


class GalleryView(DomainTemplateMixin, ListView):
    model = Gallery
    template_name = "gallery.html"
    context_object_name = "galleries"
    paginate_by = 10

    def get_queryset(self):
        # Получаем текущий домен
        current_domain = self.request.get_host()
        # Фильтруем галереи по текущему домену и другим параметрам
        queryset = Gallery.objects.filter(publishet=True, site__domain=current_domain)
        search = self.request.GET.get("search", None)

        if search and search != "None":
            queryset = queryset.filter(Q(name__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_query"] = self.request.GET.get("search", "")
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=15).first()

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
            gallery_data = [
                {
                    "name": gallery.name,
                    "description": gallery.description,
                    "author": gallery.author.username
                    if gallery.author
                    else "Администрация",
                    "create": gallery.create.strftime("%Y-%m-%d"),
                    "url": gallery.get_absolute_url(),
                    "image": gallery.image.url if gallery.image else None,
                }
                for gallery in page_obj.object_list
            ]
            return JsonResponse(
                {"galleries": gallery_data, "has_next": page_obj.has_next()}
            )

        if not self.template_name:
            raise ValueError("template_name не определен!")

        context = self.get_context_data()
        context["galleries"] = page_obj  # Данные для обычного рендеринга
        return render(request, self.template_name, context)


class GalleryDetailView(DomainTemplateMixin, DetailView):
    """Страница галереи"""

    model = Gallery
    template_name = "gallery_detail.html"
    context_object_name = "gallery"
    slug_field = "slug"

    def get_queryset(self):
        current_domain = self.request.get_host()

        # Add your domain-specific logic here to filter Blogs queryset
        filtered_page = Gallery.objects.filter(site__domain=current_domain)

        return filtered_page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gallery = context["gallery"]
        if gallery:
            context["pageinformation"] = gallery.description
            context["seo_previev"] = gallery.previev
            context["seo_title"] = gallery.title
            context["seo_description"] = gallery.metadescription
            context["seo_propertytitle"] = gallery.propertytitle
            context["seo_propertydescription"] = gallery.propertydescription
        else:
            context["pageinformation"] = None
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None
        return context


"""Услуги"""


class ServiceView(DomainTemplateMixin, ListView):
    model = Service
    template_name = "service.html"
    context_object_name = "services"
    paginate_by = 10

    def get_queryset(self):
        # Получаем текущий домен
        current_domain = self.request.get_host()
        # Фильтруем галереи по текущему домену и другим параметрам
        queryset = Service.objects.filter(publishet=True, site__domain=current_domain)
        search = self.request.GET.get("search", None)

        if search and search != "None":
            queryset = queryset.filter(Q(name__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_query"] = self.request.GET.get("search", "")
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=16).first()

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
            service_data = [
                {
                    "name": service.name,
                    "description": service.description,
                    "author": service.author.username
                    if service.author
                    else "Администрация",
                    "create": service.create.strftime("%Y-%m-%d"),
                    "url": service.get_absolute_url(),
                    "image": service.cover.url if service.cover else None,
                }
                for service in page_obj.object_list
            ]
            return JsonResponse(
                {"services": service_data, "has_next": page_obj.has_next()}
            )

        if not self.template_name:
            raise ValueError("template_name не определен!")

        context = self.get_context_data()
        context["services"] = page_obj  # Данные для обычного рендеринга
        return render(request, self.template_name, context)


class ServiceDetailView(DomainTemplateMixin, DetailView):
    """Страница услуги"""

    model = Service
    template_name = "service_detail.html"
    context_object_name = "service"
    slug_field = "slug"

    def get_queryset(self):
        return Service.objects.filter(publishet=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = context["service"]
        if service:
            context["pageinformation"] = service.description
            context["seo_previev"] = service.previev
            context["seo_title"] = service.title
            context["seo_description"] = service.metadescription
            context["seo_propertytitle"] = service.propertytitle
            context["seo_propertydescription"] = service.propertydescription
        else:
            context["pageinformation"] = None
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None
        return context


"""Прайс"""


class PriceView(DomainTemplateMixin, ListView):
    model = Price
    template_name = "price.html"
    context_object_name = "prices"
    paginate_by = 10

    def get_queryset(self):
        # Получаем текущий домен
        current_domain = self.request.get_host()
        # Фильтруем галереи по текущему домену и другим параметрам
        queryset = Price.objects.filter(publishet=True, site__domain=current_domain)
        search = self.request.GET.get("search", None)

        if search and search != "None":
            queryset = queryset.filter(Q(name__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["search_query"] = self.request.GET.get("search", "")
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=17).first()

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
            price_data = [
                {
                    "name": price.name,
                    "description": price.description,
                    "cost": price.cost,
                }
                for price in page_obj.object_list
            ]
            return JsonResponse({"prices": price_data, "has_next": page_obj.has_next()})

        if not self.template_name:
            raise ValueError("template_name не определен!")

        context = self.get_context_data()
        context["prices"] = page_obj  # Данные для обычного рендеринга
        return render(request, self.template_name, context)


"""Подписка"""


def subscribe(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Спасибо за подписку!")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        else:
            messages.error(request, "Вы уже подписаны на рассылку!")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


"""Поиск"""



# views.py

class MultiModelSearchView(DomainTemplateMixin, ListView):
    template_name = "search.html"
    context_object_name = "results"
    paginate_by = 12

    def _domain_filter(self, qs):
        current_domain = self.request.get_host()
        try:
            return qs.filter(site__domain=current_domain)
        except Exception:
            return qs

    def get_queryset(self):
        q = (self.request.GET.get("q") or "").strip()
        filters = [f for f in self.request.GET.getlist("filter") if f]  # <- чекбоксы
        if not q:
            return []

        # если не выбрано ничего или есть 'all' — считаем, что выбраны все
        if not filters or "all" in filters:
            filters = ["blogs", "products", "manufacturers", "brands", "categories", "tags"]

        results = []

        # BLOGS
        if "blogs" in filters:
            qs = Blogs.objects.annotate(
                name_lower=F.Lower("name"),
                desc_lower=F.Lower("description"),
            ).filter(
                Q(name_lower__contains=q.lower()) | Q(desc_lower__contains=q.lower())
            )
            try:
                qs = qs.filter(manufacturers__site__domain=self.request.get_host())
            except Exception:
                pass
            for obj in qs:
                obj.type = "blog"
                results.append(obj)

        # PRODUCTS
        if "products" in filters:
            qs = self._domain_filter(
                Products.objects.annotate(
                    name_lower=F.Lower("name"),
                    desc_lower=F.Lower("description"),
                ).filter(
                    Q(name_lower__contains=q.lower()) | Q(desc_lower__contains=q.lower())
                )
            )
            for obj in qs:
                obj.type = "product"
                results.append(obj)

        # CATEGORIES
        if "categories" in filters:
            qs = self._domain_filter(
                Categories.objects.annotate(
                    name_lower=F.Lower("name")
                ).filter(name_lower__contains=q.lower())
            )
            for obj in qs:
                obj.type = "category"
                results.append(obj)

        # BRANDS
        if "brands" in filters:
            qs = self._domain_filter(
                Brands.objects.annotate(
                    name_lower=F.Lower("name")
                ).filter(name_lower__contains=q.lower())
            )
            for obj in qs:
                obj.type = "brand"
                results.append(obj)

        # MANUFACTURERS
        if "manufacturers" in filters:
            qs = self._domain_filter(
                Manufacturers.objects.annotate(
                    name_lower=F.Lower("name")
                ).filter(name_lower__contains=q.lower())
            )
            for obj in qs:
                obj.type = "manufacturer"
                results.append(obj)

        # TAGS
        if "tags" in filters:
            qs = self._domain_filter(
                Tag.objects.annotate(
                    name_lower=F.Lower("name")
                ).filter(name_lower__contains=q.lower())
            )
            for obj in qs:
                obj.type = "tag"
                results.append(obj)

        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["filter"] = self.request.GET.get("filter", "")

        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=2).first()

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


"""Регистрация/Авторизация"""


def custom_logout(request):
    logout(request)
    return redirect("webmain:login")


class CustomLoginView(DomainTemplateMixin, auth_views.LoginView):
    template_name = "login.html"
    form_class = CustomAuthenticationForm

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def dispatch(self, request, *args, **kwargs):
        """Запрещаем авторизованному пользователю заходить на страницу логина"""
        if request.user.is_authenticated:
            return redirect(self.get_authenticated_redirect_url())  # Редирект в профиль

        return super().dispatch(request, *args, **kwargs)

    def get_authenticated_redirect_url(self):
        """Определяет URL для редиректа авторизованного пользователя"""
        user_type = self.request.user.type
        return (
            reverse("moderation:edit_profile")
            if user_type in (0, 2, 3)
            else reverse("useraccount:edit_profile")
        )

    def get_success_url(self):
        """Определяет, куда перенаправить пользователя после входа"""
        next_url = self.request.GET.get("next")

        # Проверяем, чтобы next не указывал на страницу логина (во избежание бесконечного цикла)
        if next_url and "login" not in next_url:
            return next_url

        return (
            self.get_authenticated_redirect_url()
        )  # Если next некорректный, ведем в профиль

    def form_invalid(self, form):
        # Обрабатываем неуспешную аутентификацию
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=5).first()

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


class SignUpView(DomainTemplateMixin, CreateView):
    form_class = SignUpForm
    template_name = "register.html"
    success_url = reverse_lazy(
        "webmain:login"
    )  # URL для редиректа после успешной регистрации

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_success_url(self):
        # Возвращаем success_url, можно переопределить логику, если нужно
        return self.success_url

    def get_form_kwargs(self):
        # Передаем дополнительные аргументы в форму, если требуется
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # Убедитесь, что форма поддерживает user
        return kwargs

    def form_valid(self, form):
        # Сохраняем пользователя
        user = form.save()
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")

        # Аутентифицируем пользователя
        user = authenticate(username=username, password=password)
        if user is not None:
            # Входим в систему
            login(self.request, user)
            return redirect(self.get_success_url())
        else:
            # Возвращаем ошибку, если аутентификация не удалась
            return HttpResponseServerError("Ошибка аутентификации")

    def get_context_data(self, **kwargs):
        # Добавляем данные для SEO
        context = super().get_context_data(**kwargs)
        current_site = get_object_or_404(Site, domain=self.request.get_host())
        seo_data = Seo.objects.filter(site=current_site, pagetype=6).first()

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


class CustomPasswordResetView(DomainTemplateMixin, PasswordResetView):
    template_name = "restore_access.html"
    email_template_name = "site/email/password_reset_email.html"
    subject_template_name = "site/email/password_reset_subject.txt"
    form_class = PasswordResetEmailForm
    success_url = reverse_lazy("useraccount:password_reset_done")

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "site/useraccount/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "site/useraccount/restore_access_user.html"
    form_class = SetPasswordFormCustom
    success_url = reverse_lazy("useraccount:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "site/useraccount/password_reset_complete.html"

class MyFeedView(LoginRequiredMixin, DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "feed.html"
    context_object_name = "homepage"
    login_url = "login"  # при необходимости поменяйте

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

class MyReviewsView(LoginRequiredMixin, DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "my_review.html"
    context_object_name = "homepage"
    login_url = "login"  # при необходимости поменяйте

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs = (
            Reviews.objects
            .filter(author=self.request.user)            # мои отзывы
            .select_related("product")                   # продукт рядом
            .prefetch_related("images")                  # картинки отзывов
            .order_by("-create")                         # свежие сверху
        )

        paginator = Paginator(qs, 10)                    # 10 на страницу
        page_obj = paginator.get_page(self.request.GET.get("page"))

        ctx["my_reviews"] = page_obj
        return ctx


class MyFaqsProductsView(LoginRequiredMixin, DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "my_faqs_product.html"
    context_object_name = "homepage"
    login_url = "login"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs = (
            FaqsProducts.objects
            .filter(user=self.request.user)         # ← ваши вопросы
            # .filter(publishet=True)               # (опционально) только опубликованные
            .select_related("product")              # подтянуть продукт
            .order_by("-create")                    # свежие сверху
        )

        paginator = Paginator(qs, 10)               # 10 на страницу
        page_obj = paginator.get_page(self.request.GET.get("page"))

        ctx["my_faqs"] = page_obj
        return ctx

class ReferralListView(LoginRequiredMixin, DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "my_referrals.html"          # свой шаблон
    context_object_name = "homepage"
    login_url = "login"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = (Profile.objects
              .filter(referral=self.request.user)
              .select_related("referral")
              .order_by("-id"))
        ctx["referrals"] = Paginator(qs, 20).get_page(self.request.GET.get("page"))
        return ctx


class SubscriberlListView(LoginRequiredMixin, DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "my_subscriber.html"
    context_object_name = "homepage"
    login_url = "login"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Список подписок на производителей текущего пользователя
        subs_qs = (
            self.request.user.manufacturers_subscriber.all()
            .order_by("name")  # если у Manufacturers есть поле name
        )
        ctx["manufacturers_subscriber"] = Paginator(subs_qs, 20).get_page(
            self.request.GET.get("page")
        )
        return ctx


class PriceReductionListView(LoginRequiredMixin, DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "my_price_reduction.html"
    context_object_name = "homepage"
    login_url = "login"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Закладки «снижение цены» (ManyToMany к Products)
        pr_qs = (
            self.request.user.price_reduction.all()
            .order_by("-id")
        )
        ctx["price_reduction"] = Paginator(pr_qs, 20).get_page(
            self.request.GET.get("page")
        )
        return ctx


class RecomendetsListView(LoginRequiredMixin, DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "my_recomendets.html"
    context_object_name = "homepage"
    login_url = "login"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # id производителей, на которых подписан пользователь
        subs_ids = list(self.request.user.manufacturers_subscriber.values_list("id", flat=True))

        if subs_ids:
            products_qs = (
                Products.objects
                .filter(
                    Q(brand_id__in=subs_ids) |          # FK -> brand
                    Q(manufacturers__in=subs_ids)       # M2M -> manufacturers
                )
                .select_related("brand")                # подтянуть бренд (FK)
                .prefetch_related("manufacturers")      # подтянуть M2M
                .distinct()
                .order_by("-create")                        # при желании поменяй сортировку
            )
        else:
            products_qs = Products.objects.none()

        ctx["recommended_products"] = Paginator(products_qs, 24).get_page(self.request.GET.get("page"))
        ctx["has_subscriptions"] = bool(subs_ids)
        return ctx