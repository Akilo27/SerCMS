import itertools
from decimal import Decimal, ROUND_DOWN
from django.utils.html import strip_tags

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse, reverse_lazy
from datetime import datetime
from django.views.generic.edit import UpdateView, FormView
from django.db.models import Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView
from django.views.generic.base import View
from collections import defaultdict
from django.http import JsonResponse, HttpResponseNotAllowed

from moderation.models import Applications
from shop.models import (
    Products,Brands,
    ProductComment,
    FaqsProducts,
    Categories,
    Reviews,
    Cart,
    ProductCommentMedia,
    SelectedProduct,
    Manufacturers,
    Variable,
    ProductsVariable,
ReviewImage,Valute,
)
from django.db import models
from django.db import transaction
from django.utils.decorators import method_decorator
from shop.forms import (OrderLookupForm,
    ReviewsForm,
    OrderForm,
    ProductCommentForm,
    SelectedProductFormSet,
)
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from urllib.parse import urlencode
from django.views.decorators.http import require_http_methods
import json
from django.contrib import messages
from django.core.paginator import EmptyPage
import traceback
from django.core.serializers.json import DjangoJSONEncoder

from useraccount.models import Profile
import logging
from django.contrib.auth.forms import AuthenticationForm
from payment.models import Order, PurchasedProduct
from django.http import QueryDict
from webmain.models import Seo, HomePage, Blogs

from webmain.models import SettingsGlobale

from integration_import.models import ImportCsv

from moderation.forms import ProductsForm, ProductsVariableFormSet

from loyalty.models import PersonalPromotion
from collections import OrderedDict

logger = logging.getLogger(__name__)
from django.utils.formats import date_format
from django.core.paginator import PageNotAnInteger
from _project.domainsmixin import DomainTemplateMixin
from django.shortcuts import redirect
from ipware import get_client_ip
import hashlib
from .templatetags.shop_tags import currency_conversion_for_products
from .utils import add_to_compare, remove_from_compare, get_compare_products
from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, F, Value
from django.db.models.functions import Replace


class OrderLookupView(DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "order_lookup.html"
    context_object_name = "homepage"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = OrderLookupForm(self.request.GET or None)

        order = None
        not_found = False

        if form.is_valid():
            q        = form.cleaned_data["q_normalized"]
            q_lower  = form.cleaned_data["q_lower"]
            digits   = form.cleaned_data["phone_digits"]
            is_digit = form.cleaned_data["q_is_digit"]
            current_site = get_current_site(self.request)

            # Базовый QS: учитываем текущий сайт И записи без site (на dev)
            base_qs = (Order.objects
                       .filter(Q(site=current_site) | Q(site__isnull=True))
                       .order_by("-created_timestamp"))

            # 1) Email
            if "@" in q_lower and order is None:
                order = base_qs.filter(customer_email__iexact=q_lower).first()

            # 2) Телефон (нормализуем в БД: убираем пробелы, +, скобки, дефисы)
            if order is None and digits:
                last4 = digits[-4:] if len(digits) >= 4 else digits
                qs_phone = base_qs.annotate(
                    phone_norm=Replace(F("phone_number"), Value(" ")
                    )
                )
                order = qs_phone.filter(
                    Q(phone_norm=digits) | Q(phone_norm__endswith=last4)
                ).first()

            # 3) Ключ (если не email и длина ≥ 6)
            if order is None and "@" not in q_lower and len(q) >= 6:
                order = base_qs.filter(key=q).first()

            # 4) № заказа (pk)
            if order is None and is_digit:
                order = base_qs.filter(pk=int(q)).first()

            not_found = (order is None)

        ctx.update({"form": form, "order": order, "not_found": not_found})
        return ctx

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            order = response.context_data.get("order")
            if order:
                return JsonResponse({
                    "ok": True,
                    "order": {
                        "id": order.pk,
                        "status": order.get_status_display(),
                        "payment_type": order.get_type_display(),
                        "created": order.created_timestamp.strftime("%Y-%m-%d %H:%M"),
                        "customer": f"{order.customer_name} {order.customer_surname}",
                        "phone": order.phone_number,
                        "email": order.customer_email,
                        "amount": order.all_amount,
                        "delivery": order.delivery_address or "",
                    }
                })
            return JsonResponse({"ok": False, "message": "Заказ не найден"}, status=404)
        return response


class ProfileSubscriptionView(View):
    def post(self, request, *args, **kwargs):
        # Декодируем JSON данные из запроса
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        manufacturer_id = data.get('manufacturer_id')
        action = data.get('action')  # 'subscribe' or 'unsubscribe'

        # Проверяем, существует ли производитель
        try:
            manufacturer = Manufacturers.objects.get(id=manufacturer_id)
        except Manufacturers.DoesNotExist:
            return JsonResponse({'error': 'Manufacturer not found'}, status=404)

        # Действие пользователя (подписка/отписка)
        if action == 'subscribe':
            request.user.manufacturers_subscriber.add(manufacturer)
            return JsonResponse({'status': 'subscribed', 'message': 'Подписка успешна'})
        elif action == 'unsubscribe':
            request.user.manufacturers_subscriber.remove(manufacturer)
            return JsonResponse({'status': 'unsubscribed', 'message': 'Отписка успешна'})
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)


from django.http import JsonResponse
from django.views.generic import View
from django.core.paginator import Paginator, EmptyPage
from django.utils.timezone import localtime
from .models import Reviews, ProductsGallery


class ReviewListView(View):
    PAGE_SIZE = 5

    def get(self, request, product_id):
        sort = request.GET.get("sort", "new")
        qs = (Reviews.objects
              .filter(product_id=product_id, publishet=True)
              .prefetch_related("images", "author"))

        if sort == "popular":
            qs = qs.order_by("-starvalue", "-create")
        else:
            qs = qs.order_by("-create")

        page_num = int(request.GET.get("page", 1) or 1)
        paginator = Paginator(qs, self.PAGE_SIZE)

        try:
            page_obj = paginator.page(page_num)
        except EmptyPage:
            return JsonResponse({"reviews": [], "has_next": False, "next_page": None})

        payload = []
        for r in page_obj.object_list:
            imgs = []
            for img in r.images.all():
                # Абсолютные URL, чтобы не было проблем с путями
                try:
                    url = request.build_absolute_uri(img.image.url)
                except Exception:
                    continue
                imgs.append({"url": url})

            payload.append({
                "id": str(r.id),
                "author": (getattr(r.author, "get_full_name", lambda: "")() or r.author.username),
                "text": r.text,
                "starvalue": r.starvalue or 0,
                "created_at": localtime(r.create).strftime("%Y-%m-%d %H:%M"),
                "images": imgs,
            })

        return JsonResponse({
            "reviews": payload,
            "has_next": page_obj.has_next(),
            "next_page": page_num + 1 if page_obj.has_next() else None,
        })

class FaqsListView(View):
    PAGE_SIZE = 5

    def get(self, request, product_id):
        qs = (FaqsProducts.objects
              .filter(product_id=product_id, publishet=True)
              .select_related("user"))

        qs = qs.order_by("-create")

        page_num = int(request.GET.get("page", 1) or 1)
        paginator = Paginator(qs, self.PAGE_SIZE)

        try:
            page_obj = paginator.page(page_num)
        except EmptyPage:
            return JsonResponse({"faqs": [], "has_next": False, "next_page": None})

        payload = []
        for q in page_obj.object_list:
            avatar = None
            if q.user and hasattr(q.user, "profile") and getattr(q.user.profile, "avatar", None):
                avatar = request.build_absolute_uri(q.user.profile.avatar.url)
            elif q.user and hasattr(q.user, "avatar") and q.user.avatar:
                avatar = request.build_absolute_uri(q.user.avatar.url)

            payload.append({
                "id": str(q.id),
                "author": q.user.get_username() if q.user else "Гость",
                "created_at": localtime(q.create).strftime("%d %B %Y г. %H:%M"),
                "question": q.question,
                "answer": q.answer,
                "avatar": avatar,
            })

        return JsonResponse({
            "faqs": payload,
            "has_next": page_obj.has_next(),
            "next_page": page_num + 1 if page_obj.has_next() else None,
        })


@require_POST
def add_compare_view(request, product_id):
    ok, msg = add_to_compare(request, product_id)
    status = 200 if ok else 400
    # Ответ для AJAX
    return JsonResponse({"ok": ok, "message": msg, "count": get_compare_count(request)}, status=status)


@require_POST
@csrf_protect
def remove_compare_view(request, product_id):
    # product_id — UUID, путь: compare/remove/<uuid:product_id>/
    remove_from_compare(request, product_id)
    count = get_compare_count(request)
    # Если AJAX — JSON, если обычная форма — редирект обратно
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"ok": True, "count": count})
    # назад на страницу сравнения (или referer)
    return redirect(request.META.get('HTTP_REFERER', 'shop:compare_page'))


def build_compare_rows(products):
    """
    Возвращает список строк для шаблона:
      [
        {"type": "section", "variable": "Размер"},
        {"type": "attr", "variable": "Размер", "attr": "Высота", "values": {<prod_id>: "180 см", ...}},
        ...
      ]

    Алгоритм:
      1) Собираем объединённый упорядоченный список групп (Variable) и их атрибутов (по имени)
      2) Для каждой пары (Variable, Attribute) строим строку с values по товарам
    """
    groups = OrderedDict()  # var_key -> {"name": var_name, "attrs": OrderedDict(attr_name -> None)}
    values_index = {}       # (prod_id, var_key, attr_name) -> str|"-"

    # Обход товаров и их атрибутов
    for p in products:
        # Можно оптимизировать, если это QuerySet: p.atribute.select_related('variable').all()
        for a in p.atribute.all().select_related('variable'):
            var = a.variable
            var_key = var.id if var else None
            var_name = var.name if var else "Без группы"

            # Регистрируем группу вариации
            if var_key not in groups:
                groups[var_key] = {"name": var_name, "attrs": OrderedDict()}

            # Регистрируем атрибут в группе (ключом используем имя)
            if a.name not in groups[var_key]["attrs"]:
                groups[var_key]["attrs"][a.name] = None

            # Значение атрибута для этого товара
            val = a.content or getattr(a, "value", "") or ""
            values_index[(str(p.id), var_key, a.name)] = val

    # Строим строки для шаблона
    rows = []
    for var_key, info in groups.items():
        rows.append({"type": "section", "variable": info["name"]})
        for attr_name in info["attrs"].keys():
            row_vals = {}
            for p in products:
                key = (str(p.id), var_key, attr_name)
                row_vals[str(p.id)] = values_index.get(key, "—")
            rows.append({
                "type": "attr",
                "variable": info["name"],
                "attr": attr_name,
                "values": row_vals,
            })
    return rows



class CompareView(DomainTemplateMixin, DetailView):
    model = HomePage
    template_name = "compare_page.html"
    context_object_name = "homepage"

    def get_object(self):
        current_domain = self.request.get_host()
        return get_object_or_404(HomePage, site__domain=current_domain)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Товары для сравнения (список/QuerySet)
        products = get_compare_products(self.request)

        # Собираем «матрицу» сравнения: секции (вариация) и строки атрибутов
        compare_rows = build_compare_rows(products)

        context["compare_products"] = products
        context["compare_rows"] = compare_rows  # ← это использует шаблон в правой колонке/таблице
        return context


def clear_compare_view(request):
    # очистка списка
    if request.user.is_authenticated:
        from .models import CompareItem
        compare = get_or_create_compare_list(request)
        CompareItem.objects.filter(compare=compare).delete()
    else:
        request.session["compare_ids"] = []
        request.session.modified = True
    messages.success(request, "Список сравнения очищен")
    return redirect("compare:page")

def get_compare_count(request):
    if request.user.is_authenticated:
        from .utils import get_or_create_compare_list
        compare = get_or_create_compare_list(request)
        return compare.items.count()
    return len(request.session.get("compare_ids", []))
















class ManufacturerProductsListView(DomainTemplateMixin, ListView):
    model = Products
    template_name = "manufacturers/product_list.html"
    context_object_name = "products"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        # Получаем параметры из запроса
        request = self.request.GET

        filters = {
            "type": request.get("type"),
            "typeofchoice": request.get("typeofchoice"),
            "slug": request.get("slug"),
            "name": request.get("name"),
            "quantity": request.get("quantity"),
            "review_rating": request.get("review_rating"),
            "review_count": request.get("review_count"),
            "review_all_sum": request.get("review_all_sum"),
            "price": request.get("price"),
            "order": request.get("order"),
            "stocks": request.get("stocks"),
            "manufacturers": request.get("manufacturers"),
            "valute": request.get("valute"),
            "site": request.get("site"),
        }

        # Применяем фильтры, где это необходимо
        if filters["type"]:
            queryset = queryset.filter(type=filters["type"])

        if filters["typeofchoice"]:
            queryset = queryset.filter(typeofchoice=filters["typeofchoice"])

        if filters["slug"]:
            queryset = queryset.filter(slug__icontains=filters["slug"])

        if filters["name"]:
            queryset = queryset.filter(name__icontains=filters["name"])

        if filters["quantity"]:
            queryset = queryset.filter(quantity=filters["quantity"])

        if filters["review_rating"]:
            queryset = queryset.filter(review_rating=filters["review_rating"])

        if filters["review_count"]:
            queryset = queryset.filter(review_count=filters["review_count"])

        if filters["review_all_sum"]:
            queryset = queryset.filter(review_all_sum=filters["review_all_sum"])

        if filters["price"]:
            queryset = queryset.filter(price=filters["price"])

        if filters["order"] in ["true", "false"]:
            queryset = queryset.filter(order=(filters["order"] == "true"))

        if request.get("search_category"):
            queryset = queryset.filter(
                category_id=request["search_category"]
            )  # если category — ForeignKey

        if filters["stocks"] in ["true", "false"]:
            queryset = queryset.filter(stocks=(filters["stocks"] == "true"))

        if filters["manufacturers"]:
            queryset = queryset.filter(manufacturers=filters["manufacturers"])

        if filters["valute"]:
            queryset = queryset.filter(valute=filters["valute"])

        if filters["site"]:
            queryset = queryset.filter(site=filters["site"])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_params"] = self.request.GET.copy()
        context["total_products"] = self.get_queryset().count()  # добавили количество
        context["categories"] = Categories.objects.all()  # <-- добавили категории
        context["site"] = Site.objects.filter(domain=self.request.get_host()).first()
        current_site = get_object_or_404(Site, domain=self.request.get_host())

        seo_data = Seo.objects.filter(site=current_site, pagetype=18).first()

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


class ManufacturerProductCreateAndEditView(UpdateView):
    model = Products
    fields = "__all__"
    template_name = "manufacturers/product_form.html"

    def get(self, request, *args, **kwargs):
        default_manufacturer = Manufacturers.objects.first()
        current_site = Site.objects.get_current()

        product = Products.objects.create(manufacturers=default_manufacturer)
        product.site.set([current_site])

        return redirect("shop:product_edit", pk=product.pk)


class ManufacturerProductUpdateView(DomainTemplateMixin, UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = "manufacturers/product_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == 3:
            return redirect("shop:product_variants_update", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("shop:products")

    def form_valid(self, form):
        product = form.save(commit=False)

        # Удаление обложки
        if self.request.POST.get("delete_cover") == "true" and product.cover:
            product.cover.delete(save=False)
            product.cover = None

        # Удаление превью
        if self.request.POST.get("delete_previev") == "true" and product.previev:
            product.previev.delete(save=False)
            product.previev = None

        # Удаление файлов из галереи
        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            ProductsGallery.objects.filter(
                id__in=delete_files_ids.split(","), products=product
            ).delete()

        product.save()
        form.save_m2m()

        # Добавляем новые файлы в галерею (здесь поле image)
        files = self.request.FILES.getlist("files")
        for file in files:
            ProductsGallery.objects.create(products=product, image=file)

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        optional_fields = [
            "quantity",
            "review_rating",
            "review_count",
            "review_all_sum",
            "manufacturer_identifier",
        ]
        for field_name in optional_fields:
            if field_name in form.fields:
                form.fields[field_name].required = False
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context["existing_files"] = self.object.productsgallery_set.all()
            context["existing_files"] = self.object.productsgallery_set.all()
            context["stock_availability"] = StockAvailability.objects.filter(
                products=self.object
            ).select_related("storage")
            context["productsprice"] = self.object.products_prices.all()
            context["costprice"] = self.object.cost_prices.all()

            context["storages"] = Storage.objects.all()  # Все склады

        return context

    def form_invalid(self, form):
        print("Ошибки формы:")
        print(form.errors.as_text())
        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(login_required(login_url="moderation:login"), name="dispatch")
class ManufacturerProductDeleteView(LoginRequiredMixin, View):
    success_url = reverse_lazy("shop:products")

    def post(self, request):
        data = json.loads(request.body)
        blogs_ids = data.get("blogs_ids", [])
        if blogs_ids:
            Products.objects.filter(id__in=blogs_ids).delete()
        return JsonResponse({"status": "success", "redirect": self.success_url})


class ManufacturerProductUpdateVariateView(DomainTemplateMixin, UpdateView):
    model = Products
    form_class = ProductsForm
    template_name = "manufacturers/product_variable_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.type == 1:
            return redirect("moderation:product_edit", pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("moderation:products")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        optional_fields = [
            "quantity",
            "review_rating",
            "review_count",
            "review_all_sum",
            "manufacturer_identifier",
        ]
        for field in optional_fields:
            if field in form.fields:
                form.fields[field].required = False
        return form

    def get_variable_formset(self):
        return ProductsVariableFormSet(
            self.request.POST or None,
            self.request.FILES or None,
            queryset=ProductsVariable.objects.filter(products=self.object),
        )

    def form_valid(self, form):
        product = form.save(commit=False)

        # Обработка удаления обложки
        if self.request.POST.get("delete_cover") == "true" and product.cover:
            product.cover.delete(save=False)
            product.cover = None

        # Обработка удаления превью
        if self.request.POST.get("delete_previev") == "true" and product.previev:
            product.previev.delete(save=False)
            product.previev = None

        # Обработка удаления изображений из галереи
        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            ProductsGallery.objects.filter(
                id__in=delete_files_ids.split(","), products=product
            ).delete()

        product.save()
        form.save_m2m()

        # Сохраняем файлы в галерею
        for file in self.request.FILES.getlist("files"):
            ProductsGallery.objects.create(products=product, image=file)

        # Обработка формы вариаций
        variable_formset = self.get_variable_formset()
        if variable_formset.is_valid():
            instances = variable_formset.save(commit=False)
            for instance in instances:
                instance.products = product
                instance.save()
            variable_formset.save_m2m()

            # Удалённые формы
            for deleted in variable_formset.deleted_objects:
                deleted.delete()
        else:
            return self.render_to_response(
                self.get_context_data(form=form, variable_formset=variable_formset)
            )

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def form_valid(self, form):
        product = form.save(commit=False)

        # Удаление файлов
        if self.request.POST.get("delete_cover") == "true" and product.cover:
            product.cover.delete(save=False)
            product.cover = None

        if self.request.POST.get("delete_previev") == "true" and product.previev:
            product.previev.delete(save=False)
            product.previev = None

        delete_files_ids = self.request.POST.get("delete_files", "")
        if delete_files_ids:
            ProductsGallery.objects.filter(
                id__in=delete_files_ids.split(","), products=product
            ).delete()

        product.save()
        form.save_m2m()

        for file in self.request.FILES.getlist("files"):
            ProductsGallery.objects.create(products=product, image=file)

        # --- Форма вариаций ---
        variable_formset = self.get_variable_formset()

        if variable_formset.is_valid():
            instances = variable_formset.save(commit=False)
            for instance in instances:
                instance.products = product
                instance.save()
            variable_formset.save_m2m()

            for deleted in variable_formset.deleted_objects:
                deleted.delete()
        else:
            # Вывод ошибок в консоль
            print("❌ Ошибки в variable_formset:")
            for i, form in enumerate(variable_formset.forms):
                if form.errors:
                    print(f"Форма #{i + 1} ошибки: {form.errors.as_text()}")

            if variable_formset.non_form_errors():
                print("Общие ошибки формы:", variable_formset.non_form_errors())

            messages.error(
                self.request,
                "Ошибки при сохранении вариаций. Проверьте заполненные поля.",
            )
            return self.render_to_response(
                self.get_context_data(form=form, variable_formset=variable_formset)
            )

        messages.success(self.request, "Изменения сохранены")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        context["existing_files"] = product.productsgallery_set.all()
        context["stock_availability"] = StockAvailability.objects.filter(
            products=product
        ).select_related("storage")
        context["productsprice"] = product.products_prices.all()
        context["costprice"] = product.cost_prices.all()
        context["productvariables"] = ProductsVariable.objects.filter(
            products=product
        ).prefetch_related("attribute")

        if "variable_formset" not in kwargs:
            variable_formset = self.get_variable_formset()
            context["variable_formset"] = variable_formset
        else:
            context["variable_formset"] = kwargs["variable_formset"]

        # Для добавления через JS
        context["empty_form"] = ProductsVariableFormSet(
            queryset=ProductsVariable.objects.none()
        ).empty_form
        context["storages"] = Storage.objects.all()

        return context


class ManufacturerEditView(DomainTemplateMixin, View):
    template_name = "manufacturers/edit.html"

    def get(self, request, slug):
        manufacturer = get_object_or_404(Manufacturers, slug=slug)
        return render(request, self.template_name, {"manufacturer": manufacturer})

    def post(self, request, slug):
        manufacturer = get_object_or_404(Manufacturers, slug=slug)

        manufacturer.name = request.POST.get("name")
        manufacturer.description = request.POST.get("description")
        manufacturer.email = request.POST.get("email")
        manufacturer.phone = request.POST.get("phone")
        manufacturer.company_name = request.POST.get("company_name")
        manufacturer.company_inn = request.POST.get("company_inn")
        manufacturer.company_director = request.POST.get("company_director")
        manufacturer.company_adress = request.POST.get("company_adress")
        manufacturer.title = request.POST.get("title")
        manufacturer.metadescription = request.POST.get("metadescription")
        manufacturer.propertytitle = request.POST.get("propertytitle")
        manufacturer.propertydescription = request.POST.get("propertydescription")

        if request.FILES.get("image"):
            manufacturer.image = request.FILES["image"]
        if request.FILES.get("cover"):
            manufacturer.cover = request.FILES["cover"]
        if request.FILES.get("previev"):
            manufacturer.previev = request.FILES["previev"]

        manufacturer.save()

        return redirect("manufacturer_edit", slug=manufacturer.slug)


# функция конвертации валют для фильтров
def convert_to_product_currency(price, product_currency, user_currency):
    if product_currency == user_currency:
        return Decimal(price)
    conversion_rate = Decimal(product_currency.relationship) / Decimal(
        user_currency.relationship
    )
    converted_price = Decimal(price) * conversion_rate
    return converted_price.quantize(Decimal("1.00"), rounding=ROUND_DOWN)





class ManufacturersBlogView(DomainTemplateMixin, DetailView):
    model = Manufacturers
    template_name = "site/trendsup/manufacturers_details_blog.html"  # ← путь внутри templates/
    context_object_name = "manufacturer"
    paginate_by = 12

    def get_object(self):
        current_domain = self.request.get_host()
        # Фильтруем по домену, чтобы не открыть чужой магазин
        return get_object_or_404(Manufacturers, slug=self.kwargs["slug"], site__domain=current_domain)

    def get_blogs_queryset(self):
        m = self.get_object()
        return (Blogs.objects
                .filter(manufacturers=m)
                .select_related("author", "manufacturers")
                .order_by("-create"))

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        queryset  = self.get_blogs_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_obj  = paginator.get_page(request.GET.get("page", 1))

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            blogs_data = []
            for blog in page_obj.object_list:
                clean_descr = strip_tags(getattr(blog, "description", "") or "")
                short_descr = (clean_descr[:150] + "…") if len(clean_descr) > 150 else clean_descr
                blogs_data.append({
                    "name": blog.name,
                    "description": short_descr,
                    "author": getattr(getattr(blog, "author", None), "username", "Администрация"),
                    "create": getattr(blog, "create", None).strftime("%Y-%m-%d") if getattr(blog, "create", None) else "",
                    "url": blog.get_absolute_url() if hasattr(blog, "get_absolute_url") else "",
                    "image": blog.image.url if getattr(blog, "image", None) else None,
                })
            return JsonResponse({"blogs": blogs_data, "has_next": page_obj.has_next()})

        ctx = self.get_context_data()
        ctx["blogs"] = page_obj
        ctx["is_paginated"] = page_obj.has_other_pages()
        return render(request, self.template_name, ctx)


class ManufacturersView(DomainTemplateMixin, DetailView):
    """Страницы"""

    model = Manufacturers
    template_name = "manufacturers_details.html"
    context_object_name = "manufacturer"
    paginate_by = 32

    def get_object(self):
        # Получаем производителя по слагу из URL
        return get_object_or_404(Manufacturers, slug=self.kwargs["slug"])



    def get_queryset(self):
        manufacturer = get_object_or_404(Manufacturers, slug=self.kwargs["slug"])
        queryset = Products.objects.filter(manufacturers=manufacturer, price__gt=0)
        current_domain = self.request.get_host()
        filtered_products = queryset.filter(site__domain=current_domain)

        rating = self.request.GET.getlist("rating")
        selected_categories = self.request.GET.getlist("category")
        type_id = self.request.GET.get("type", None)
        filter_type = self.request.GET.get("filter", None)
        min_price = self.request.GET.get("min_price", None)
        max_price = self.request.GET.get("max_price", None)
        filterprice = self.request.GET.get("filterprice", None)

        if selected_categories:
            filtered_products = filtered_products.filter(
                category__id__in=selected_categories
            )

        if rating:
            filtered_products = filtered_products.filter(
                review_rating__in=[int(r) for r in rating]
            )

        if type_id:
            filtered_products = filtered_products.filter(type_id=type_id)

        selected_atributes = self.request.GET.getlist("atribute", [])
        if selected_atributes:
            filtered_atributes = [int(a) for a in selected_atributes if a.strip() != ""]
            if filtered_atributes:
                filtered_products = filtered_products.filter(
                    atribute__id__in=filtered_atributes
                )

        if filter_type:
            if filter_type == "1":
                filtered_products = filtered_products.order_by("name")
            elif filter_type == "2":
                filtered_products = filtered_products.order_by("-create")
            elif filter_type == "3":
                filtered_products = filtered_products.order_by("create")

        # Получаем ключ браузера и сессии
        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key

        # Поиск корзины без создания
        cart = None
        if self.request.user.is_authenticated:
            cart = Cart.objects.filter(
                site__domain=current_domain, user=self.request.user
            ).first()
        else:
            cart = Cart.objects.filter(
                site__domain=current_domain, session_key=session_key
            ).first()

        user_currency = cart.valute if cart else None

        if (min_price or max_price) and user_currency:
            final_filtered_products = []
            for product in filtered_products:
                product_price_in_user_currency = convert_to_product_currency(
                    product.price, product.valute, user_currency
                )
                if min_price and product_price_in_user_currency < Decimal(min_price):
                    continue
                if max_price and product_price_in_user_currency > Decimal(max_price):
                    continue
                final_filtered_products.append(product)
            filtered_products = final_filtered_products

        if filterprice and user_currency:
            if filterprice == "4":
                filtered_products = sorted(
                    filtered_products,
                    key=lambda p: convert_to_product_currency(
                        p.price, p.valute, user_currency
                    ),
                    reverse=True,
                )
            elif filterprice == "5":
                filtered_products = sorted(
                    filtered_products,
                    key=lambda p: convert_to_product_currency(
                        p.price, p.valute, user_currency
                    ),
                )

        return filtered_products


    def get(self, request, *args, **kwargs):
        self.template_name = self.get_template_names()[0]

        # Сохраняем один раз отфильтрованный queryset
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        self.object_list = page_obj.object_list  # это важно!
        # ✅ AJAX-ответ
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                products_data = []
                for product in self.object_list:  # <-- используем self.object_list

                    products_data.append(
                        {
                            "id": product.id,
                            "name": product.name,
                            "description": product.description,
                            "price": float(product.price) if product.price else None,
                            "image": product.image.url if product.image else None,
                            "url": product.get_absolute_url()
                            if hasattr(product, "get_absolute_url")
                            else None,
                            "category": product.category.name
                            if product.category
                            else None,
                            "rating": float(product.review_rating)
                            if product.review_rating
                            else None,
                        }
                    )

                return JsonResponse(
                    {"products": products_data, "has_next": page_obj.has_next()},
                    encoder=DjangoJSONEncoder,
                )

            except Exception as e:
                print("Ошибка сериализации AJAX-ответа:")
                print(traceback.format_exc())
                return JsonResponse({"error": str(e)}, status=500)

        # 📄 HTML-ответ
        self.object = self.get_object()
        context = self.get_context_data()
        context["products"] = page_obj
        context['action'] = True
        return render(request, self.template_name, context)




    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filtered_products = self.get_queryset()
        current_domain = self.request.get_host()
        manufacture = self.object
        settings = SettingsGlobale.objects.get(site__domain=current_domain)

        # Устанавливаем текущие значения цен
        current_min_price = self.request.GET.get("min_price", 0)
        current_max_price = self.request.GET.get("max_price", "")
        context["manufacture"] = manufacture
        context["default_min_price"] = 0
        context["current_min_price"] = current_min_price
        context["current_max_price"] = current_max_price

        # Получение данных браузера и сессии
        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key

        # Поиск корзины без создания
        cart = None
        if self.request.user.is_authenticated:
            cart = Cart.objects.filter(
                site__domain=current_domain, user=self.request.user
            ).first()
        else:
            cart = Cart.objects.filter(
                site__domain=current_domain, session_key=session_key
            ).first()

        context["valute"] = cart.valute if cart else None

        # Характеристики товаров
        variables_with_atributes = Variable.objects.filter(
            variabletype__in=[1, 3], site__domain=current_domain
        ).prefetch_related("atribute_set")
        context["variables_with_atributes"] = variables_with_atributes

        selected_attributes = {
            key: value
            for key, value in self.request.GET.items()
            if key.startswith("atribute")
        }
        context["selected_attributes"] = selected_attributes

        context["selected_ratings"] = self.request.GET.getlist("rating", [])
        context["selected_type"] = self.request.GET.get("typ", "")
        context["selected_filter"] = self.request.GET.get("filter", "")
        context["all_categories"] = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=Count("products"))
        context["categories"] = Categories.objects.filter(site__domain=current_domain)
        context["selected_categories"] = self.request.GET.getlist("category", [])

        categories_with_count = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=models.Count("products"))
        context["categories_with_count"] = categories_with_count

        # Закладки и заявки пользователя
        if self.request.user.is_authenticated:
            person = get_object_or_404(Profile, id=self.request.user.id)
            bookmarks = person.bookmark.all()
            bookmarked_product_ids = set(bookmarks.values_list("id", flat=True))
            context["is_bookmarked"] = [
                product
                for product in filtered_products
                if product.id in bookmarked_product_ids
            ]

            user_applications = Applications.objects.filter(user=person)
            # application_product_ids = set(user_applications.values_list("products__id", flat=True))
            # context['application_exists'] = [product for product in filtered_products if
            #                                  product.id in application_product_ids]

        # Добавляем текущие параметры фильтрации в контекст
        current_filters = QueryDict(mutable=True)
        current_filters.update(
            {
                "min_price": self.request.GET.get("min_price", ""),
                "max_price": self.request.GET.get("max_price", ""),
                "rating": self.request.GET.getlist("rating"),
                "category": self.request.GET.getlist("category"),
                "type": self.request.GET.get("type", ""),
                "filter": self.request.GET.get("filter", ""),
                "atribute": self.request.GET.getlist("atribute"),
            }
        )
        context["current_filters"] = urlencode(current_filters, doseq=True)

        # Проверка наличия фильтров
        context["has_filters"] = bool(
            self.request.GET.get("min_price")
            or self.request.GET.get("max_price")
            or self.request.GET.getlist("rating")
            or self.request.GET.getlist("category")
            or self.request.GET.get("type")
            or self.request.GET.get("filter")
            or self.request.GET.getlist("atribute")
        )

        # Пагинация
        paginator = Paginator(filtered_products, 12)
        page = self.request.GET.get("page")

        try:
            paginated_products = paginator.page(page)
        except PageNotAnInteger:
            paginated_products = paginator.page(1)
        except EmptyPage:
            paginated_products = paginator.page(paginator.num_pages)

        context["products"] = paginated_products
        context["paginator"] = paginator
        context["page_obj"] = paginated_products

        return context


class ProductsActionListView(DomainTemplateMixin, ListView):
    """Страницы"""

    model = Products
    template_name = "catalog.html"
    context_object_name = "products"
    paginate_by = 21

    def get_queryset(self):
        queryset = Products.objects.filter(stocks=True)

        current_domain = self.request.get_host()

        # ⬅️ фильтрация сразу по domain + stocks
        filtered_products = queryset.filter(site__domain=current_domain, stocks=True)

        rating = self.request.GET.getlist("rating")
        selected_categories = self.request.GET.getlist("category")
        type_id = self.request.GET.get("type", None)
        filter_type = self.request.GET.get("filter", None)
        min_price = self.request.GET.get("min_price", None)
        max_price = self.request.GET.get("max_price", None)
        filterprice = self.request.GET.get("filterprice", None)

        if selected_categories:
            filtered_products = filtered_products.filter(
                category__id__in=selected_categories
            )

        if rating:
            filtered_products = filtered_products.filter(
                review_rating__in=[int(r) for r in rating]
            )

        if type_id:
            filtered_products = filtered_products.filter(type_id=type_id)

        selected_attributes = [
            value
            for key, value in self.request.GET.items()
            if key.startswith("atribute")
        ]
        if selected_attributes:
            filtered_atributes = [
                int(a) for a in selected_attributes if a.strip() != ""
            ]
            if filtered_atributes:
                filtered_products = filtered_products.filter(
                    productsvariable__attribute__id__in=filtered_atributes
                ).distinct()

        if min_price or max_price:
            user_currency = self.get_user_currency()
            filtered_products = self.filter_by_price(
                filtered_products, min_price, max_price, user_currency
            )

        if filter_type:
            if filter_type == "1":
                filtered_products = filtered_products.order_by("name")
            elif filter_type == "2":
                filtered_products = filtered_products.order_by("-create")
            elif filter_type == "3":
                filtered_products = filtered_products.order_by("create")

        if filterprice:
            if filterprice == "4":
                filtered_products = filtered_products.order_by("-price")
            elif filterprice == "5":
                filtered_products = filtered_products.order_by("price")

        return filtered_products

    def paginate_queryset(self, queryset, page_size):
        """Обрабатываем пагинацию, чтобы избежать 404 и ошибки PageNotAnInteger"""
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get("page")

        try:
            page_number = int(page)
            if page_number < 1:
                page_number = 1
        except (TypeError, ValueError):
            page_number = 1

        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        is_paginated = page_obj.has_other_pages()
        return paginator, page_obj, page_obj.object_list, is_paginated

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_domain = self.request.get_host()

        settings = SettingsGlobale.objects.get(site__domain=current_domain)

        product_max_price = 100000
        product_min_price = 0

        try:
            jsontemplate = json.loads(settings.jsontemplate)
            if isinstance(jsontemplate, list) and jsontemplate:
                fields = jsontemplate[0].get("fields", {})
                max_price_block = fields.get("max_price")
                min_price_block = fields.get("min_price")

                if max_price_block:
                    product_max_price = int(
                        max_price_block.get("field", product_max_price)
                    )
                if min_price_block:
                    product_min_price = int(
                        min_price_block.get("field", product_min_price)
                    )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        current_min_price = self.request.GET.get("min_price", product_min_price)
        current_max_price = self.request.GET.get("max_price", product_max_price)

        context["default_min_price"] = product_min_price
        context["default_max_price"] = product_max_price
        context["current_min_price"] = current_min_price
        context["current_max_price"] = current_max_price

        context["valute"] = (
            self.get_user_currency() if hasattr(self, "get_user_currency") else "KGS"
        )


        context["all_manufacturers"] = Manufacturers.objects.all()
        context["all_brands"] = Brands.objects.all()
        context["selected_manufacturers"] = self.request.GET.getlist("manufacturer", [])
        context["selected_brands"] = self.request.GET.getlist("brand", [])

        context["all_categories"] = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=Count("products"))

        context["current_filters"] = urlencode(
            {
                "min_price": current_min_price,
                "max_price": current_max_price,
                "rating": self.request.GET.getlist("rating"),
                "category": self.request.GET.getlist("category"),
                "type": self.request.GET.get("type", ""),
                "filter": self.request.GET.get("filter", ""),
                "atribute": self.request.GET.getlist("atribute"),
            },
            doseq=True,
        )

        variables_with_atributes = Variable.objects.filter(
            variabletype__in=[1, 3], site__domain=current_domain
        ).prefetch_related("atribute_set")
        context["variables_with_atributes"] = variables_with_atributes

        context["selected_attributes"] = {
            key: value
            for key, value in self.request.GET.items()
            if key.startswith("atribute")
        }
        context["selected_ratings"] = self.request.GET.getlist("rating", [])
        context["selected_filter"] = self.request.GET.get("filter", "")
        context["selected_categories"] = self.request.GET.getlist("category", [])

        context["all_categories"] = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=Count("products"))

        context["current_filters"] = urlencode(
            {
                "min_price": current_min_price,
                "max_price": current_max_price,
                "rating": self.request.GET.getlist("rating"),
                "category": self.request.GET.getlist("category"),
                "type": self.request.GET.get("type", ""),
                "filter": self.request.GET.get("filter", ""),
                "atribute": self.request.GET.getlist("atribute"),
            },
            doseq=True,
        )

        context["has_filters"] = bool(
            self.request.GET.get("min_price")
            or self.request.GET.get("max_price")
            or self.request.GET.getlist("rating")
            or self.request.GET.getlist("category")
            or self.request.GET.get("type")
            or self.request.GET.get("filter")
            or self.request.GET.getlist("atribute")
        )

        return context

    def get_user_currency(self):
        """Функция для получения валюты пользователя."""
        current_domain = self.request.get_host()
        current_site = Site.objects.get(domain=current_domain)
        session = self.request.session

        if not session.session_key:
            session.save()
        session_key = session.session_key

        # Получаем browser_key для неавторизованных
        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

        # 1. Пробуем найти корзину по session_key и site
        cart = Cart.objects.filter(session_key=session_key, site=current_site).first()

        # 2. Если не нашли — пробуем по пользователю (если авторизован)
        if not cart and self.request.user.is_authenticated:
            cart = Cart.objects.filter(
                user=self.request.user, site=current_site
            ).first()

        # 3. Если всё ещё не нашли — создаём (если нужно)
        if not cart:
            cart = Cart.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                session_key=session_key,
                browser_key=browser_key,
                amount=Decimal("0"),
                site=current_site,  # <-- здесь используем FK, а не many-to-many
            )

        return cart.valute

    def filter_by_price(self, queryset, min_price, max_price, currency):
        try:
            min_price = float(min_price) if min_price else None
            max_price = float(max_price) if max_price else None
        except ValueError:
            return queryset  # Если значения некорректные — возвращаем без фильтрации

        # Предположим, цена хранится в одной валюте, или ты знаешь как конвертировать
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def get(self, request, *args, **kwargs):
        self.template_name = self.get_template_names()[0]

        # Сохраняем один раз отфильтрованный queryset
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        self.object_list = page_obj.object_list  # это важно!

        # ✅ AJAX-ответ
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                products_data = []
                for product in self.object_list:  # <-- используем self.object_list

                    products_data.append(
                        {
                            "name": product.name,
                            "description": product.description,
                            "price": float(product.price) if product.price else None,
                            "image": product.image.url if product.image else None,
                            "url": product.get_absolute_url()
                            if hasattr(product, "get_absolute_url")
                            else None,
                            "category": product.category.name
                            if product.category
                            else None,
                            "rating": float(product.review_rating)
                            if product.review_rating
                            else None,
                        }
                    )

                return JsonResponse(
                    {"products": products_data, "has_next": page_obj.has_next()},
                    encoder=DjangoJSONEncoder,
                )

            except Exception as e:
                print("Ошибка сериализации AJAX-ответа:")
                print(traceback.format_exc())
                return JsonResponse({"error": str(e)}, status=500)

        # 📄 HTML-ответ
        context = self.get_context_data()
        context["products"] = page_obj
        context['action'] = True
        return render(request, self.template_name, context)

from uuid import UUID
from decimal import Decimal, ROUND_HALF_UP


class ProductsByIdsView(View):
    def get(self, request, *args, **kwargs):
        ids = request.GET.get("ids", "")
        ids_list = []

        # фильтруем только валидные UUID
        for i in ids.split(","):
            i = i.strip()
            if not i:
                continue
            try:
                ids_list.append(UUID(i))
            except ValueError:
                continue

        products = Products.objects.filter(id__in=ids_list)

        try:
            # ---------- Валюта ----------
            cart_valute = None
            cart_obj = getattr(request, "cart", None)
            if cart_obj is not None and getattr(cart_obj, "valute", None):
                cart_valute = cart_obj.valute

            if cart_valute is None:
                vid = request.session.get("valute_id")
                vkey = request.session.get("valute_key")
                try:
                    if vid:
                        cart_valute = Valute.objects.filter(id=vid).first()
                    elif vkey:
                        cart_valute = Valute.objects.filter(key=vkey).first()
                except Exception:
                    cart_valute = None

            if cart_valute is None:
                try:
                    cart_valute = Valute.objects.filter(default=True).first()
                except Exception:
                    cart_valute = None

            rel = Decimal("1")
            allowance_mult = Decimal("1")
            if cart_valute:
                try:
                    rel = Decimal(cart_valute.relationship or 1)
                except Exception:
                    rel = Decimal("1")
                try:
                    allowance = Decimal(cart_valute.allowance or 0)
                except Exception:
                    allowance = Decimal("0")
                allowance_mult = (Decimal("100") + allowance) / Decimal("100")

            if cart_valute and getattr(cart_valute, "key", None):
                currency_code = str(cart_valute.key)
            elif cart_valute and getattr(cart_valute, "name", None):
                currency_code = str(cart_valute.name)
            else:
                currency_code = "KGS"

            # ---------- данные ----------
            products_data = []
            user_bookmarks = []
            if request.user.is_authenticated:
                user_bookmarks = set(
                    request.user.bookmark.values_list("id", flat=True)
                )

            for product in products:
                # атрибуты
                attrs = [
                    {
                        "variable_name": attr.variable.name if attr.variable else "",
                        "name": attr.name,
                        "content": attr.content,
                    }
                    for attr in product.atribute.all()
                    if attr.variable and attr.variable.variablestype in [2, 3]
                ]

                # галерея
                try:
                    # пробуем разные related_name
                    if hasattr(product, "gallery"):
                        gallery_images = [g.image.url for g in product.gallery.all() if g.image]
                    elif hasattr(product, "productsgallery_set"):
                        gallery_images = [g.image.url for g in product.productsgallery_set.all() if g.image]
                    else:
                        gallery_images = []
                except Exception:
                    gallery_images = []

                # главное изображение
                main_image = product.image.url if getattr(product, "image", None) else (
                    gallery_images[0] if gallery_images else None
                )

                # variation_slug
                variation_slug = ""
                try:
                    variable = product.productsvariable_set.filter(defaultposition=True).first()
                    if not variable:
                        variable = product.productsvariable_set.first()
                    if variable:
                        variation_slug = variable.slug
                except Exception:
                    variation_slug = ""

                # отзывы
                rc = getattr(product, "review_count", None)
                if rc is None:
                    try:
                        if hasattr(product, "reviews"):
                            rc = product.reviews.count()
                        elif hasattr(product, "review_set"):
                            rc = product.review_set.count()
                        else:
                            rc = 0
                    except Exception:
                        rc = 0

                # рейтинг
                try:
                    rating_val = float(product.review_rating) if product.review_rating else 0.0
                except Exception:
                    rating_val = 0.0

                # 💰 конвертация цены
                converted_price = None
                base_price = getattr(product, "price", None)
                if base_price is not None:
                    try:
                        base_dec = Decimal(str(base_price))
                        conv = (base_dec * rel * allowance_mult).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        converted_price = float(conv)
                    except Exception:
                        try:
                            converted_price = float(base_price)
                        except Exception:
                            converted_price = None

                products_data.append({
                    "id": str(product.id),
                    "name": product.name,
                    "price": converted_price,
                    "image": main_image,
                    "images": gallery_images,
                    "url": product.get_absolute_url() if hasattr(product, "get_absolute_url") else None,
                    "atribute": attrs,
                    "category": [c.slug for c in product.category.all()] if hasattr(product, "category") else None,
                    "rating": rating_val,
                    "review_count": int(rc),
                    "is_bookmarked": product.id in user_bookmarks,
                    "variation_slug": variation_slug,
                    "stocks": product.stocks,
                    "reklama": bool(getattr(product, "reklama", False)),
                })

            return JsonResponse(
                {
                    "products": products_data,
                    "currency": currency_code,
                },
                encoder=DjangoJSONEncoder,
            )

        except Exception:
            import traceback
            print("Ошибка сериализации AJAX-ответа:")
            print(traceback.format_exc())
            return JsonResponse({"error": "serialization error"}, status=500)

class ProductsListView(DomainTemplateMixin, ListView):
    """Страницы"""

    model = Products
    template_name = "catalog.html"
    context_object_name = "products"
    paginate_by = 21

    def get_queryset(self):
        queryset = super().get_queryset() or Products.objects.all()

        current_domain = self.request.get_host()
        filtered_products = queryset.filter(site__domain=current_domain)

        rating = self.request.GET.getlist("rating")
        selected_categories = self.request.GET.getlist("category")
        type_id = self.request.GET.get("type", None)
        filter_type = self.request.GET.get("filter", None)
        min_price = self.request.GET.get("min_price", None)
        max_price = self.request.GET.get("max_price", None)
        filterprice = self.request.GET.get("filterprice", None)

        if selected_categories:
            filtered_products = filtered_products.filter(
                category__id__in=selected_categories
            )

        if rating:
            filtered_products = filtered_products.filter(
                review_rating__in=[int(r) for r in rating]
            )

        manufacturers_ids = self.request.GET.getlist("manufacturer")
        if manufacturers_ids:
            filtered_products = filtered_products.filter(manufacturers__id__in=manufacturers_ids)

        brands_ids = self.request.GET.getlist("brand")
        if brands_ids:
            filtered_products = filtered_products.filter(brand__id__in=brands_ids)

        if type_id:
            filtered_products = filtered_products.filter(type_id=type_id)

        selected_attributes = [
            value
            for key, value in self.request.GET.items()
            if key.startswith("atribute")
        ]
        if selected_attributes:
            filtered_atributes = [
                int(a) for a in selected_attributes if a.strip() != ""
            ]
            if filtered_atributes:
                filtered_products = filtered_products.filter(
                    productsvariable__attribute__id__in=filtered_atributes
                ).distinct()

        if min_price or max_price:
            user_currency = self.get_user_currency()
            filtered_products = self.filter_by_price(
                filtered_products, min_price, max_price, user_currency
            )

        if filter_type:
            if filter_type == "1":
                filtered_products = filtered_products.order_by("name")
            elif filter_type == "2":
                filtered_products = filtered_products.order_by("-create")
            elif filter_type == "3":
                filtered_products = filtered_products.order_by("create")

        if filterprice:
            if filterprice == "4":
                filtered_products = filtered_products.order_by("-price")
            elif filterprice == "5":
                filtered_products = filtered_products.order_by("price")

        return filtered_products

    def paginate_queryset(self, queryset, page_size):
        """Обрабатываем пагинацию, чтобы избежать 404 и ошибки PageNotAnInteger"""
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get("page")

        try:
            page_number = int(page)
            if page_number < 1:
                page_number = 1
        except (TypeError, ValueError):
            page_number = 1

        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        is_paginated = page_obj.has_other_pages()
        return paginator, page_obj, page_obj.object_list, is_paginated

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_domain = self.request.get_host()

        settings = SettingsGlobale.objects.get(site__domain=current_domain)

        product_max_price = 100000
        product_min_price = 0

        try:
            jsontemplate = json.loads(settings.jsontemplate)
            if isinstance(jsontemplate, list) and jsontemplate:
                fields = jsontemplate[0].get("fields", {})
                max_price_block = fields.get("max_price")
                min_price_block = fields.get("min_price")

                if max_price_block:
                    product_max_price = int(
                        max_price_block.get("field", product_max_price)
                    )
                if min_price_block:
                    product_min_price = int(
                        min_price_block.get("field", product_min_price)
                    )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        context["products_count"] = self.get_queryset().count()

        current_min_price = self.request.GET.get("min_price", product_min_price)
        current_max_price = self.request.GET.get("max_price", product_max_price)

        context["default_min_price"] = product_min_price
        context["default_max_price"] = product_max_price
        context["current_min_price"] = current_min_price
        context["current_max_price"] = current_max_price

        context["valute"] = (
            self.get_user_currency() if hasattr(self, "get_user_currency") else "KGS"
        )

        variables_with_atributes = Variable.objects.filter(
            variabletype__in=[1, 3], site__domain=current_domain
        ).prefetch_related("atribute_set")
        context["variables_with_atributes"] = variables_with_atributes

        context["selected_attributes"] = {
            key: value
            for key, value in self.request.GET.items()
            if key.startswith("atribute")
        }
        context["selected_ratings"] = self.request.GET.getlist("rating", [])
        context["selected_filter"] = self.request.GET.get("filter", "")
        context["selected_categories"] = self.request.GET.getlist("category", [])
        context["all_manufacturers"] = Manufacturers.objects.all()
        context["all_brands"] = Brands.objects.all()
        context["selected_manufacturers"] = self.request.GET.getlist("manufacturer", [])
        context["selected_brands"] = self.request.GET.getlist("brand", [])

        context["all_categories"] = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=Count("products"))

        context["current_filters"] = urlencode(
            {
                "min_price": current_min_price,
                "max_price": current_max_price,
                "rating": self.request.GET.getlist("rating"),
                "category": self.request.GET.getlist("category"),
                "type": self.request.GET.get("type", ""),
                "filter": self.request.GET.get("filter", ""),
                "atribute": self.request.GET.getlist("atribute"),
            },
            doseq=True,
        )

        context["has_filters"] = bool(
            self.request.GET.get("min_price")
            or self.request.GET.get("max_price")
            or self.request.GET.getlist("rating")
            or self.request.GET.getlist("category")
            or self.request.GET.get("type")
            or self.request.GET.get("filter")
            or self.request.GET.getlist("atribute")
        )

        return context

    def get_user_currency(self):
        """Функция для получения валюты пользователя без создания корзины."""
        current_domain = self.request.get_host()
        current_site = Site.objects.get(domain=current_domain)
        session = self.request.session

        if not session.session_key:
            session.save()
        session_key = session.session_key

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

        cart = Cart.objects.filter(session_key=session_key, site=current_site).first()

        if not cart and self.request.user.is_authenticated:
            cart = Cart.objects.filter(user=self.request.user, site=current_site).first()

        return cart.valute if cart and cart.valute else "KGS"

    def filter_by_price(self, queryset, min_price, max_price, currency):
        try:
            min_price = float(min_price) if min_price else None
            max_price = float(max_price) if max_price else None
        except ValueError:
            return queryset  # Если значения некорректные — возвращаем без фильтрации

        # Предположим, цена хранится в одной валюте, или ты знаешь как конвертировать
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def get(self, request, *args, **kwargs):
        from decimal import Decimal, ROUND_HALF_UP

        self.template_name = self.get_template_names()[0]

        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        self.object_list = page_obj.object_list  # важно для AJAX

        # ✅ AJAX-ответ
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                # ---------- Валюта корзины ----------
                cart_valute = None
                cart_obj = getattr(request, "cart", None)
                if cart_obj is not None and getattr(cart_obj, "valute", None):
                    cart_valute = cart_obj.valute

                # (необязательно) подстраховка через сессию
                if cart_valute is None:
                    vid = request.session.get("valute_id")
                    vkey = request.session.get("valute_key")
                    try:
                        if vid:
                            cart_valute = Valute.objects.filter(id=vid).first()
                        elif vkey:
                            cart_valute = Valute.objects.filter(key=vkey).first()
                    except Exception:
                        cart_valute = None

                # дефолтная валюта
                if cart_valute is None:
                    try:
                        cart_valute = Valute.objects.filter(default=True).first()
                    except Exception:
                        cart_valute = None

                # коэффициенты конвертации
                rel = Decimal("1")
                allowance_mult = Decimal("1")
                if cart_valute:
                    try:
                        rel = Decimal(cart_valute.relationship or 1)
                    except Exception:
                        rel = Decimal("1")
                    try:
                        allowance = Decimal(cart_valute.allowance or 0)
                    except Exception:
                        allowance = Decimal("0")
                    allowance_mult = (Decimal("100") + allowance) / Decimal("100")

                # строковый код валюты для фронта (как раньше)
                if cart_valute and getattr(cart_valute, "key", None):
                    currency_code = str(cart_valute.key)
                elif cart_valute and getattr(cart_valute, "name", None):
                    currency_code = str(cart_valute.name)
                else:
                    currency_code = "KGS"  # запасной вариант

                # ---------- данные ----------
                products_data = []
                user_bookmarks = []
                if request.user.is_authenticated:
                    user_bookmarks = set(
                        request.user.bookmark.values_list("id", flat=True)
                    )

                for product in self.object_list:
                    # атрибуты
                    attrs = [
                        {
                            "variable_name": attr.variable.name if attr.variable else "",
                            "name": attr.name,
                            "content": attr.content,
                        }
                        for attr in product.atribute.all()
                        if attr.variable and attr.variable.variablestype in [2, 3]
                    ]

                    # галерея
                    try:
                        gallery_images = [g.image.url for g in product.galleries.all() if g.image]
                    except Exception:
                        gallery_images = []

                    # главное изображение
                    main_image = product.image.url if getattr(product, "image", None) else (
                        gallery_images[0] if gallery_images else None
                    )

                    # variation_slug
                    variation_slug = ""
                    try:
                        variable = product.productsvariable_set.filter(defaultposition=True).first()
                        if not variable:
                            variable = product.productsvariable_set.first()
                        if variable:
                            variation_slug = variable.slug
                    except Exception:
                        variation_slug = ""

                    # отзывы
                    rc = getattr(product, "review_count", None)
                    if rc is None:
                        try:
                            if hasattr(product, "reviews"):
                                rc = product.reviews.count()
                            elif hasattr(product, "review_set"):
                                rc = product.review_set.count()
                            else:
                                rc = 0
                        except Exception:
                            rc = 0

                    # рейтинг
                    try:
                        rating_val = float(product.review_rating) if product.review_rating else 0.0
                    except Exception:
                        rating_val = 0.0

                    # 💰 конвертация цены: base * relationship * (1 + allowance/100)
                    converted_price = None
                    base_price = getattr(product, "price", None)
                    if base_price is not None:
                        try:
                            base_dec = Decimal(str(base_price))
                            conv = (base_dec * rel * allowance_mult).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                            converted_price = float(conv)
                        except Exception:
                            try:
                                converted_price = float(base_price)
                            except Exception:
                                converted_price = None

                    products_data.append({
                        "id": str(product.id),
                        "name": product.name,
                        "price": converted_price,  # уже сконвертированная цена
                        "image": main_image,
                        "images": gallery_images,
                        "url": product.get_absolute_url() if hasattr(product, "get_absolute_url") else None,
                        "atribute": attrs,
                        "category": [category.slug for category in product.category.all()] if hasattr(product, "category") else None,
                        "rating": rating_val,
                        "review_count": int(rc),
                        "is_bookmarked": product.id in user_bookmarks,
                        "variation_slug": variation_slug,
                        'stocks': product.stocks,
                        "reklama": bool(getattr(product, "reklama", False)),
                    })

                return JsonResponse(
                    {
                        "products": products_data,
                        "has_next": page_obj.has_next(),
                        "currency": currency_code,  # ✅ строка, а не объект — больше не будет [object Object]
                    },
                    encoder=DjangoJSONEncoder,
                )

            except Exception:
                import traceback
                print("Ошибка сериализации AJAX-ответа:")
                print(traceback.format_exc())
                return JsonResponse({"error": "serialization error"}, status=500)

        # 📄 HTML-ответ
        context = self.get_context_data()
        context["products"] = page_obj
        return render(request, self.template_name, context)


class ProductsListMenuView(DomainTemplateMixin, ListView):
    model = Products
    template_name = "menu.html"
    context_object_name = "products"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset() or Products.objects.all()
        current_domain = self.request.get_host()
        filtered_products = queryset.filter(site__domain=current_domain)

        # ---- Фильтры ----
        rating = self.request.GET.getlist("rating")
        selected_categories = self.request.GET.getlist("category")
        type_id = self.request.GET.get("type")
        filter_type = self.request.GET.get("filter")
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        filterprice = self.request.GET.get("filterprice")

        if selected_categories:
            filtered_products = filtered_products.filter(category__id__in=selected_categories)

        if rating:
            filtered_products = filtered_products.filter(review_rating__in=[int(r) for r in rating])

        manufacturers_ids = self.request.GET.getlist("manufacturer")
        if manufacturers_ids:
            filtered_products = filtered_products.filter(manufacturers__id__in=manufacturers_ids)

        brands_ids = self.request.GET.getlist("brand")
        if brands_ids:
            filtered_products = filtered_products.filter(brand__id__in=brands_ids)

        if type_id:
            filtered_products = filtered_products.filter(type_id=type_id)

        selected_attributes = [
            value for key, value in self.request.GET.items() if key.startswith("atribute")
        ]
        if selected_attributes:
            filtered_atributes = [int(a) for a in selected_attributes if a.strip() != ""]
            if filtered_atributes:
                filtered_products = filtered_products.filter(
                    productsvariable__attribute__id__in=filtered_atributes
                ).distinct()

        if min_price or max_price:
            user_currency = self.get_user_currency()
            filtered_products = self.filter_by_price(
                filtered_products, min_price, max_price, user_currency
            )

        if filter_type:
            if filter_type == "1":
                filtered_products = filtered_products.order_by("name")
            elif filter_type == "2":
                filtered_products = filtered_products.order_by("-create")
            elif filter_type == "3":
                filtered_products = filtered_products.order_by("create")

        if filterprice:
            if filterprice == "4":
                filtered_products = filtered_products.order_by("-price")
            elif filterprice == "5":
                filtered_products = filtered_products.order_by("price")

        return filtered_products.prefetch_related("category")

    def paginate_queryset(self, queryset, page_size):
        """Обрабатываем пагинацию, чтобы избежать 404 и ошибки PageNotAnInteger"""
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get("page")

        try:
            page_number = int(page)
            if page_number < 1:
                page_number = 1
        except (TypeError, ValueError):
            page_number = 1

        try:
            page_obj = paginator.page(page_number)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        is_paginated = page_obj.has_other_pages()
        return paginator, page_obj, page_obj.object_list, is_paginated

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_domain = self.request.get_host()
        settings = SettingsGlobale.objects.get(site__domain=current_domain)

        # ---- Ценовые блоки ----
        product_max_price = 100000
        product_min_price = 0
        try:
            jsontemplate = json.loads(settings.jsontemplate)
            if isinstance(jsontemplate, list) and jsontemplate:
                fields = jsontemplate[0].get("fields", {})
                max_price_block = fields.get("max_price")
                min_price_block = fields.get("min_price")
                if max_price_block:
                    product_max_price = int(max_price_block.get("field", product_max_price))
                if min_price_block:
                    product_min_price = int(min_price_block.get("field", product_min_price))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        current_min_price = self.request.GET.get("min_price", product_min_price)
        current_max_price = self.request.GET.get("max_price", product_max_price)

        context["default_min_price"] = product_min_price
        context["default_max_price"] = product_max_price
        context["current_min_price"] = current_min_price
        context["current_max_price"] = current_max_price
        context["valute"] = self.get_user_currency()

        context["variables_with_atributes"] = Variable.objects.filter(
            variabletype__in=[1, 3], site__domain=current_domain
        ).prefetch_related("atribute_set")
        context["selected_attributes"] = {
            key: value for key, value in self.request.GET.items() if key.startswith("atribute")
        }
        context["selected_ratings"] = self.request.GET.getlist("rating", [])
        context["selected_filter"] = self.request.GET.get("filter", "")
        context["selected_categories"] = self.request.GET.getlist("category", [])
        context["all_manufacturers"] = Manufacturers.objects.all()
        context["all_brands"] = Brands.objects.all()
        context["selected_manufacturers"] = self.request.GET.getlist("manufacturer", [])
        context["selected_brands"] = self.request.GET.getlist("brand", [])
        context["all_categories"] = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=Count("products"))

        context["current_filters"] = urlencode(
            {
                "min_price": current_min_price,
                "max_price": current_max_price,
                "rating": self.request.GET.getlist("rating"),
                "category": self.request.GET.getlist("category"),
                "type": self.request.GET.get("type", ""),
                "filter": self.request.GET.get("filter", ""),
                "atribute": self.request.GET.getlist("atribute"),
            },
            doseq=True,
        )
        context["has_filters"] = bool(
            self.request.GET.get("min_price")
            or self.request.GET.get("max_price")
            or self.request.GET.getlist("rating")
            or self.request.GET.getlist("category")
            or self.request.GET.get("type")
            or self.request.GET.get("filter")
            or self.request.GET.getlist("atribute")
        )

        # ---- Группировка по категориям ----
        grouped_products = defaultdict(list)
        for product in context["products"]:
            for category in product.category.all():
                grouped_products[category].append(product)
        context["grouped_products"] = dict(grouped_products)

        return context

    def get_user_currency(self):
        current_domain = self.request.get_host()
        current_site = Site.objects.get(domain=current_domain)
        session = self.request.session
        if not session.session_key:
            session.save()
        session_key = session.session_key
        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        cart = Cart.objects.filter(session_key=session_key, site=current_site).first()
        if not cart and self.request.user.is_authenticated:
            cart = Cart.objects.filter(user=self.request.user, site=current_site).first()
        return cart.valute if cart and cart.valute else "KGS"

    def filter_by_price(self, queryset, min_price, max_price, currency):
        try:
            min_price = float(min_price) if min_price else None
            max_price = float(max_price) if max_price else None
        except ValueError:
            return queryset
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def get(self, request, *args, **kwargs):
        self.template_name = self.get_template_names()[0]
        queryset = self.get_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        self.object_list = page_obj.object_list

        # AJAX
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                products_data = []
                for product in self.object_list:
                    products_data.append(
                        {
                            "name": product.name,
                            "description": getattr(product, "description", ""),
                            "price": float(product.price) if product.price else None,
                            "image": product.image.url if product.image else None,
                            "url": product.get_absolute_url() if hasattr(product, "get_absolute_url") else None,
                            "category": [cat.name for cat in product.category.all()],
                            "rating": float(product.review_rating) if getattr(product, "review_rating", None) else None,
                        }
                    )
                return JsonResponse({"products": products_data, "has_next": page_obj.has_next()})
            except Exception as e:
                print(traceback.format_exc())
                return JsonResponse({"error": str(e)}, status=500)

        # HTML
        context = self.get_context_data()
        context["products"] = page_obj
        return render(request, self.template_name, context)


def load_category_content(request, category_id):
    category = get_object_or_404(Categories, id=category_id)
    children = category.children.all()
    products = category.products_rekomendet.all()
    user = request.user
    client_ip, _ = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
    session_key = request.session.session_key
    if user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            site__domain=request.get_host(), user=request.user
        )
    else:
        # Combine session_key and browser_key to identify the cart
        cart, created = Cart.objects.get_or_create(
            browser_key=browser_key,
            site__domain=request.get_host(),
            defaults={"session_key": session_key},
        )  # Получаем корзину по session_key

    current_valute = (
        cart.valute
    )  # Получаем текущую валюту из сессии или используем дефолтное значение

    products_data = [
        {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "image_url": product.image.url if product.image else "",
            "price": currency_conversion_for_products(
                request, product.price, product.valute.id
            ),  # Применяем конвертацию
            "quantity": product.quantity,
            "order": product.order,
        }
        for product in products
    ]

    content = {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "children": [
            {
                "id": child.id,
                "name": child.name,
                "slug": child.slug,
                "children": [
                    {
                        "id": grandchild.id,
                        "name": grandchild.name,
                        "slug": grandchild.slug,
                    }
                    for grandchild in child.children.all()
                ],
            }
            for child in children
        ],
        "products": products_data,
        "banners": [
            {"id": banner.id, "image_url": banner.image.url, "slug": banner.slug}
            for banner in category.banner_set.all()
        ]
        if hasattr(category, "banner_set")
        else [],
        "current_valute": current_valute.icon_code,
    }

    return JsonResponse(content)


class CategoriesView(DomainTemplateMixin, DetailView):
    """Страницы"""

    model = Categories
    template_name = "category.html"
    context_object_name = "category"
    paginate_by = 32

    def get_queryset(self):
        return Categories.objects.filter(site__domain=self.request.get_host())

    def get_object(self, queryset=None):
        if not hasattr(self, 'object'):
            self.object = super().get_object(queryset)
        return self.object

    def get(self, request, *args, **kwargs):
        from decimal import Decimal, ROUND_HALF_UP

        self.template_name = self.get_template_names()[0]
        self.object = self.get_object()

        queryset = Products.objects.filter(category=self.get_object())

        paginator = Paginator(queryset, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        self.object_list = page_obj.object_list  # важно для AJAX
        print(self.object_list, self.object)
        # ✅ AJAX-ответ
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            try:
                # ---------- Валюта корзины ----------
                cart_valute = None
                cart_obj = getattr(request, "cart", None)
                if cart_obj is not None and getattr(cart_obj, "valute", None):
                    cart_valute = cart_obj.valute

                # (необязательно) подстраховка через сессию
                if cart_valute is None:
                    vid = request.session.get("valute_id")
                    vkey = request.session.get("valute_key")
                    try:
                        if vid:
                            cart_valute = Valute.objects.filter(id=vid).first()
                        elif vkey:
                            cart_valute = Valute.objects.filter(key=vkey).first()
                    except Exception:
                        cart_valute = None

                # дефолтная валюта
                if cart_valute is None:
                    try:
                        cart_valute = Valute.objects.filter(default=True).first()
                    except Exception:
                        cart_valute = None

                # коэффициенты конвертации
                rel = Decimal("1")
                allowance_mult = Decimal("1")
                if cart_valute:
                    try:
                        rel = Decimal(cart_valute.relationship or 1)
                    except Exception:
                        rel = Decimal("1")
                    try:
                        allowance = Decimal(cart_valute.allowance or 0)
                    except Exception:
                        allowance = Decimal("0")
                    allowance_mult = (Decimal("100") + allowance) / Decimal("100")

                # строковый код валюты для фронта (как раньше)
                if cart_valute and getattr(cart_valute, "key", None):
                    currency_code = str(cart_valute.key)
                elif cart_valute and getattr(cart_valute, "name", None):
                    currency_code = str(cart_valute.name)
                else:
                    currency_code = "KGS"  # запасной вариант

                # ---------- данные ----------
                products_data = []
                user_bookmarks = []
                if request.user.is_authenticated:
                    user_bookmarks = set(
                        request.user.bookmark.values_list("id", flat=True)
                    )

                for product in self.object_list:
                    # атрибуты
                    attrs = [
                        {
                            "variable_name": attr.variable.name if attr.variable else "",
                            "name": attr.name,
                            "content": attr.content,
                        }
                        for attr in product.atribute.all()
                        if attr.variable and attr.variable.variablestype in [2, 3]
                    ]

                    # галерея
                    try:
                        gallery_images = [g.image.url for g in product.galleries.all() if g.image]
                    except Exception:
                        gallery_images = []

                    # главное изображение
                    main_image = product.image.url if getattr(product, "image", None) else (
                        gallery_images[0] if gallery_images else None
                    )

                    # variation_slug
                    variation_slug = ""
                    try:
                        variable = product.productsvariable_set.filter(defaultposition=True).first()
                        if not variable:
                            variable = product.productsvariable_set.first()
                        if variable:
                            variation_slug = variable.slug
                    except Exception:
                        variation_slug = ""

                    # отзывы
                    rc = getattr(product, "review_count", None)
                    if rc is None:
                        try:
                            if hasattr(product, "reviews"):
                                rc = product.reviews.count()
                            elif hasattr(product, "review_set"):
                                rc = product.review_set.count()
                            else:
                                rc = 0
                        except Exception:
                            rc = 0

                    # рейтинг
                    try:
                        rating_val = float(product.review_rating) if product.review_rating else 0.0
                    except Exception:
                        rating_val = 0.0

                    # 💰 конвертация цены: base * relationship * (1 + allowance/100)
                    converted_price = None
                    base_price = getattr(product, "price", None)
                    if base_price is not None:
                        try:
                            base_dec = Decimal(str(base_price))
                            conv = (base_dec * rel * allowance_mult).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                            converted_price = float(conv)
                        except Exception:
                            try:
                                converted_price = float(base_price)
                            except Exception:
                                converted_price = None

                    products_data.append({
                        "id": str(product.id),
                        "name": product.name,
                        "price": converted_price,  # уже сконвертированная цена
                        "image": main_image,
                        "images": gallery_images,
                        "url": product.get_absolute_url() if hasattr(product, "get_absolute_url") else None,
                        "atribute": attrs,
                        "category": [category.slug for category in product.category.all()] if hasattr(product, "category") else None,
                        "rating": rating_val,
                        "review_count": int(rc),
                        "is_bookmarked": product.id in user_bookmarks,
                        "variation_slug": variation_slug,
                        'stocks': product.stocks,
                        "reklama": bool(getattr(product, "reklama", False)),
                    })

                return JsonResponse(
                    {
                        "products": products_data,
                        "has_next": page_obj.has_next(),
                        "currency": currency_code,  # ✅ строка, а не объект — больше не будет [object Object]
                    },
                    encoder=DjangoJSONEncoder,
                )

            except Exception:
                import traceback
                print("Ошибка сериализации AJAX-ответа:")
                print(traceback.format_exc())
                return JsonResponse({"error": "serialization error"}, status=500)

        context = self.get_context_data()
        context["products"] = page_obj
        return render(request, self.template_name, context)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object = self.get_object()
        print(self.get_object())
        category = self.object
        current_domain = self.request.get_host()
        categoryget = self.request.GET.getlist("category")
        if not categoryget:
            filtered_products = Products.objects.filter(
                category=category, site__domain=current_domain, price__gt=0
            )
        else:
            filtered_products = Products.objects.filter(
                category__id__in=categoryget, site__domain=current_domain, price__gt=0
            )

        rating = self.request.GET.getlist("rating")
        type_id = self.request.GET.get("type")
        filter_type = self.request.GET.get("filter")
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")
        filterprice = self.request.GET.get("filterprice", None)
        selected_attributes = self.request.GET.getlist("atribute", [])

        if rating:
            filtered_products = filtered_products.filter(
                review_rating__in=[int(r) for r in rating]
            )
        if type_id:
            filtered_products = filtered_products.filter(type_id=type_id)
        if selected_attributes:
            filtered_attributes = [int(a) for a in selected_attributes if a.strip()]
            if filtered_attributes:
                filtered_products = filtered_products.filter(
                    atribute__id__in=filtered_attributes
                )

        if filter_type:
            if filter_type == "1":
                filtered_products = filtered_products.order_by("name")
            elif filter_type == "2":
                filtered_products = filtered_products.order_by("-create")
            elif filter_type == "3":
                filtered_products = filtered_products.order_by("create")

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=self.request.user
            )
        else:
            # Combine session_key and browser_key to identify the cart
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )

        user_currency = cart.valute

        if min_price or max_price:
            final_filtered_products = []
            for product in filtered_products:
                product_price_in_user_currency = convert_to_product_currency(
                    product.price, product.valute, user_currency
                )
                if min_price and product_price_in_user_currency < Decimal(min_price):
                    continue
                if max_price and product_price_in_user_currency > Decimal(max_price):
                    continue
                final_filtered_products.append(product)
            filtered_products = final_filtered_products
        if filterprice:
            if filterprice == "4":
                filtered_products = sorted(
                    filtered_products,
                    key=lambda p: convert_to_product_currency(
                        p.price, p.valute, user_currency
                    ),
                    reverse=True,
                )
            elif filterprice == "5":
                filtered_products = sorted(
                    filtered_products,
                    key=lambda p: convert_to_product_currency(
                        p.price, p.valute, user_currency
                    ),
                )

        context["products"] = filtered_products

        variables_with_attributes = Variable.objects.filter(
            variabletype__in=[1, 3], site__domain=current_domain
        ).prefetch_related("atribute_set")

        variables_with_atributes = Variable.objects.filter(
            variabletype__in=[1, 3], site__domain=current_domain
        ).prefetch_related("atribute_set")

        context["variables_with_atributes"] = variables_with_atributes

        current_domain = self.request.get_host()

        settings = SettingsGlobale.objects.get(site__domain=current_domain)

        # Значения по умолчанию
        product_max_price = 100000
        product_min_price = 0

        # Парсинг json-поля jsontemplate
        try:
            jsontemplate = json.loads(settings.jsontemplate)
            if isinstance(jsontemplate, list) and jsontemplate:
                fields = jsontemplate[0].get("fields", {})
                max_price_block = fields.get("max_price")
                min_price_block = fields.get("min_price")

                if max_price_block:
                    product_max_price = int(
                        max_price_block.get("field", product_max_price)
                    )
                if min_price_block:
                    product_min_price = int(
                        min_price_block.get("field", product_min_price)
                    )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        # Значения из GET или из json
        current_min_price = self.request.GET.get("min_price", product_min_price)
        current_max_price = self.request.GET.get("max_price", product_max_price)

        context["default_min_price"] = product_min_price
        context["default_max_price"] = product_max_price
        context["current_min_price"] = current_min_price
        context["current_max_price"] = current_max_price

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=self.request.user
            )
        else:
            # Combine session_key and browser_key to identify the cart
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )
        currency = cart.valute
        context["valute"] = currency

        selected_atributes = [
            value
            for key, value in self.request.GET.items()
            if key.startswith("atribute")
        ]

        if selected_atributes:
            filtered_atributes = [int(a) for a in selected_atributes if a.strip() != ""]
            if filtered_atributes:
                filtered_products = filtered_products.filter(
                    productsvariable__attribute__id__in=filtered_atributes
                ).distinct()

        context["variables_with_attributes"] = variables_with_attributes
        selected_attributes = {
            key: value
            for key, value in self.request.GET.items()
            if key.startswith("atribute")
        }
        context["selected_attributes"] = selected_attributes
        context["selected_ratings"] = rating

        context["selected_type"] = self.request.GET.get("type", "")
        context["selected_filter"] = self.request.GET.get("filter", "")

        context["categories"] = Categories.objects.filter(site__domain=current_domain)
        context["selected_categories"] = self.request.GET.getlist("category", [])

        context["all_manufacturers"] = Manufacturers.objects.all()
        context["all_brands"] = Brands.objects.all()
        context["selected_manufacturers"] = self.request.GET.getlist("manufacturer", [])
        context["selected_brands"] = self.request.GET.getlist("brand", [])

        context["all_categories"] = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=Count("products"))

        context["current_filters"] = urlencode(
            {
                "min_price": current_min_price,
                "max_price": current_max_price,
                "rating": self.request.GET.getlist("rating"),
                "category": self.request.GET.getlist("category"),
                "type": self.request.GET.get("type", ""),
                "filter": self.request.GET.get("filter", ""),
                "atribute": self.request.GET.getlist("atribute"),
            },
            doseq=True,
        )

        categories_with_count = Categories.objects.filter(
            site__domain=current_domain
        ).annotate(product_count=models.Count("products"))
        context["categories_with_count"] = categories_with_count

        if self.request.user.is_authenticated:
            person = get_object_or_404(Profile, id=self.request.user.id)
            bookmarks = person.bookmark.all()
            bookmarked_product_ids = set(bookmarks.values_list("id", flat=True))
            context["is_bookmarked"] = [
                product
                for product in filtered_products
                if product.id in bookmarked_product_ids
            ]

            # user_applications = Applications.objects.filter(user=person)
            # application_product_ids = set(user_applications.values_list("products__id", flat=True))
            # context['application_exists'] = [
            #     product for product in filtered_products if product.id in application_product_ids
            # ]

        context["current_filters"] = urlencode(
            {
                "min_price": self.request.GET.get("min_price", ""),
                "max_price": self.request.GET.get("max_price", ""),
                "rating": rating,
                "category": self.request.GET.getlist("category"),
                "type": self.request.GET.get("type", ""),
                "filter": self.request.GET.get("filter", ""),
                "atribute": selected_attributes,
            },
            doseq=True,
        )

        context["has_filters"] = bool(
            self.request.GET.get("min_price")
            or self.request.GET.get("max_price")
            or rating
            or self.request.GET.getlist("category")
            or self.request.GET.get("type")
            or self.request.GET.get("filter")
            or selected_attributes
        )

        # Пагинация
        paginator = Paginator(filtered_products, 18)  # 10 продуктов на страницу
        page = self.request.GET.get("page")
        try:
            paginated_products = paginator.page(page)
        except PageNotAnInteger:
            paginated_products = paginator.page(1)
        except EmptyPage:
            paginated_products = paginator.page(paginator.num_pages)

        context["products"] = paginated_products
        context["paginator"] = paginator
        context["page_obj"] = paginated_products

        return context


class TogglePriceReductionView(View):
    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Products, id=product_id)

        if product in request.user.price_reduction.all():
            # Если продукт уже в закладках, удаляем
            request.user.price_reduction.remove(product)
            is_added = False
        else:
            # Если продукта нет, добавляем
            request.user.price_reduction.add(product)
            is_added = True

        return JsonResponse({
            'is_added': is_added,
            'message': 'Продукт добавлен в закладки.' if is_added else 'Продукт удалён из закладок.'
        })




def convert_price_via_base(price, from_valute: Valute, to_valute: Valute) -> Decimal:
    """
    КОНВЕРСИЯ ЧЕРЕЗ БАЗОВУЮ ВАЛЮТУ.

    Ожидания по модели:
      - Valute.relationship = Сколько единиц базовой валюты за 1 единицу ЭТОЙ валюты.
        (пример: USD.relationship = 100 => 1 USD = 100 базовых единиц; RUB.relationship = 1)
      - Valute.allowance = наценка целевой валюты в %, применяется ПОСЛЕ конверсии в целевую.
    Формула:
      price_base    = price * from.relationship
      price_target  = price_base / to.relationship
      price_target *= (1 + to.allowance/100)
    """
    price = Decimal(str(price))

    # Страховки
    if not from_valute or not to_valute:
        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    from_rel = Decimal(from_valute.relationship or 1)
    to_rel = Decimal(to_valute.relationship or 1)
    if to_rel == 0:
        # на случай «битой» валюты
        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 1) в базовую
    price_base = price * from_rel
    # 2) из базовой в целевую
    price_target = price_base / to_rel
    # 3) наценка целевой валюты
    allowance_factor = (Decimal(100) + Decimal(to_valute.allowance or 0)) / Decimal(100)
    price_target = price_target * allowance_factor

    return price_target.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)




class ProductsVariableDetailView(DomainTemplateMixin, DetailView):
    model = Products
    template_name = "product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]

        variable_slug = self.kwargs["variation_slug"]
        slug = self.kwargs["slug"]

        selected_attribute = []
        product_variable_obj = get_object_or_404(ProductsVariable, slug=variable_slug)
        for attributes in product_variable_obj.attribute.all():
            selected_attribute.append(attributes.slug)

        context["product_variable"] = product_variable_obj
        context["selected_attributes"] = selected_attribute
        context["selfslug"] = slug
        context["variation_slug"] = variable_slug
        context["product_variables"] = product.productsvariable_set.all()

        attributes_by_variable = {}
        all_variables_for_product = []
        current_site = get_current_site(self.request)

        for product_variable in product.productsvariable_set.all():
            for attribute in product_variable.attribute.all():
                variable = attribute.variable
                if variable not in attributes_by_variable:
                    attributes_by_variable[variable] = set()
                attributes_by_variable[variable].add(attribute)

        for variable in attributes_by_variable:
            attributes_by_variable[variable] = list(attributes_by_variable[variable])

        context["attributes_by_variable"] = attributes_by_variable

        # === Связанные товары ===
        shop_category_products = Products.get_shop_category_products(product, limit=8)
        context["top_product"] = shop_category_products
        related_or_higher_products = Products.get_products_from_category_or_above(product, limit=8)
        context["trends_product"] = related_or_higher_products

        for item in product.productsvariable_set.all():
            for attribute in item.attribute.all():
                variable_data = {
                    "ProductsVariable_slug": item.slug,
                    "Attribute_variable_slug": attribute.variable.slug,
                    "Attribute_slug": attribute.slug,
                }
                all_variables_for_product.append(variable_data)
        context["all_variables_for_product"] = all_variables_for_product

        # ==== Корзина и валюта ====
        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key

        if self.request.user.is_authenticated:
            cart = Cart.objects.filter(user=self.request.user, site=current_site).first()
            if not cart:
                cart = Cart.objects.filter(browser_key=browser_key, site=current_site).first()
                if cart:
                    cart.user = self.request.user
                    cart.save()
                else:
                    cart = Cart.objects.create(user=self.request.user, site=current_site)
        else:
            cart = Cart.objects.filter(browser_key=browser_key, site=current_site).first()
            if not cart:
                cart = Cart.objects.create(
                    browser_key=browser_key, session_key=session_key, site=current_site
                )

        context["valute"] = cart.valute

        # ==== Конвертируем product.variable_json и возвращаем строкой в том же формате ====
        variable_json_str = product.variable_json
        if variable_json_str:
            try:
                data = json.loads(variable_json_str)

                # исходная валюта товара: берём product.valute, fallback — валюта корзины/дефолт
                try:
                    from_valute = product.valute
                except Exception:
                    from_valute = None
                if not from_valute:
                    from_valute = cart.valute or Valute.objects.filter(default=True).first()

                for item in data:
                    # price в JSON — строка (например "667.00"), сохраняем этот формат
                    raw_price = item.get("price", "0")
                    new_price = convert_price_via_base(raw_price, from_valute, cart.valute)
                    item["price"] = f"{new_price:.2f}"

                variable_json_str = json.dumps(data, ensure_ascii=False)

            except Exception as e:
                print("Ошибка обработки variable_json:", e)

        context["variable_json"] = variable_json_str

        # ==== Остальной контекст ====
        if self.request.user.is_authenticated:
            user = self.request.user
            person = get_object_or_404(Profile, id=user.id)
            context["is_bookmarked"] = person.bookmark.all()

            checkout_exists = Order.objects.filter(
                user=user, selectedproduct__product=product, reviews=False
            ).exists()
            context["show_reviews_form"] = checkout_exists
            if checkout_exists:
                context["reviews_form"] = ReviewsForm
        else:
            context["is_bookmarked"] = False
            context["login_form"] = AuthenticationForm()

        if product:
            context["pageinformation"] = product.description
            context["seo_previev"] = product.title
            context["seo_title"] = product.title
            context["seo_description"] = product.metadescription
            context["seo_propertytitle"] = product.title
            context["seo_propertydescription"] = product.description
        else:
            context["pageinformation"] = None

        return context

    def get_queryset(self):
        current_domain = self.request.get_host()
        return Products.objects.filter(site__domain=current_domain)

class ProductsDetailView(DomainTemplateMixin, DetailView):
    model = Products
    template_name = "product_detail.html"
    context_object_name = "product"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)  # исправлено имя переменной
        product = self.object

        if product.type == 1:
            return self.render_to_response(context)
        else:
            variable = ProductsVariable.objects.filter(
                products=product, defaultposition=True
            ).first()
            if not variable:
                variable = ProductsVariable.objects.filter(products=product).first()
            variation_slug = variable.slug
            return redirect(
                reverse(
                    "shop:products_variable",
                    kwargs={"slug": product.slug, "variation_slug": variation_slug},
                )
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context["product"]
        current_site = get_current_site(self.request)
        attributes_by_variable = {}

        for product_variable in product.productsvariable_set.all():
            for attribute in product_variable.attribute.all():
                variable = attribute.variable
                if variable not in attributes_by_variable:
                    attributes_by_variable[variable] = set()
                attributes_by_variable[variable].add(attribute)

        for variable in attributes_by_variable:
            attributes_by_variable[variable] = list(attributes_by_variable[variable])

        context["attributes_by_variable"] = attributes_by_variable

        # Reviews Pagination
        reviews = product.reviews.filter(publishet=True)
        reviews_paginator = Paginator(reviews, 10)
        reviews_page = self.request.GET.get("reviews_page", 1)

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key

        # Ищем корзину по session_key и site, без создания новой
        cart = (
            Cart.objects.filter(session_key=session_key, site=current_site).first()
            or Cart.objects.filter(browser_key=browser_key, site=current_site).first()
        )

        # Если корзина найдена, добавляем её валюту в контекст
        if cart:
            context["valute"] = cart.valute
        else:
            context["cart_error"] = "Корзина не найдена"

        # Обработка пагинации для отзывов
        try:
            reviews_page = int(reviews_page)
        except ValueError:
            reviews_page = 1

        try:
            reviews_paginated = reviews_paginator.page(reviews_page)
        except PageNotAnInteger:
            reviews_paginated = reviews_paginator.page(1)
        except EmptyPage:
            reviews_paginated = reviews_paginator.page(reviews_paginator.num_pages)

        context["reviews"] = reviews_paginated

        # FAQs Pagination
        faqs = FaqsProducts.objects.filter(publishet=True)
        faqs_paginator = Paginator(faqs, 10)
        faqs_page = self.request.GET.get("faqs_page", 1)
        shop_category_products = Products.get_shop_category_products(product, limit=8)
        context["top_product"] = shop_category_products

        # Для варианта 2 (любые 8 товаров этой категории или выше)
        related_or_higher_products = Products.get_products_from_category_or_above(product, limit=8)
        context["trends_product"] = related_or_higher_products


        try:
            faqs_page = int(faqs_page)
        except ValueError:
            faqs_page = 1

        try:
            faqs_paginated = faqs_paginator.page(faqs_page)
        except PageNotAnInteger:
            faqs_paginated = faqs_paginator.page(1)
        except EmptyPage:
            faqs_paginated = faqs_paginator.page(faqs_paginator.num_pages)

        context["faqs"] = faqs_paginated

        # Other context setup
        if self.request.user.is_authenticated:
            user = self.request.user
            person = get_object_or_404(Profile, id=user.id)
            context["is_bookmarked"] = person.bookmark.all()
            user_applications = Applications.objects.filter(user=person)

            # Проверка SelectedProduct
            selected_product_exists = SelectedProduct.objects.filter(
                user=user, product=product, status=2, reviews=False
            ).exists()

            context["show_reviews_form"] = selected_product_exists
            if selected_product_exists:
                context["reviews_form"] = ReviewsForm()
        else:
            context["is_bookmarked"] = False
            context["login_form"] = AuthenticationForm()

        # SEO и информация о странице
        if product:
            context["pageinformation"] = product.description
            context["seo_previev"] = product.title
            context["seo_title"] = product.title
            context["seo_description"] = product.metadescription
            context["seo_propertytitle"] = product.title
            context["seo_propertydescription"] = product.description
        else:
            context["pageinformation"] = None

        return context

    def get_queryset(self):
        # Filter the queryset for the "blog" view based on the current domain
        current_domain = self.request.get_host()

        # Add your domain-specific logic here to filter Blogs queryset
        filtered_product = Products.objects.filter(site__domain=current_domain)

        return filtered_product


#
#
# class UserUploadCSVView(DomainTemplateMixin, FormView):
#     template_name = 'upload_csv.html'
#     form_class = CSVUploadForm
#     success_url = '/shop_edit/'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         # Pagination setup
#         import_csv_list = ImportCsv.objects.all()
#         paginator = Paginator(import_csv_list, 10)
#         page = self.request.GET.get('page')
#
#         try:
#             import_csv = paginator.page(page)
#         except PageNotAnInteger:
#             import_csv = paginator.page(1)
#         except EmptyPage:
#             import_csv = paginator.page(paginator.num_pages)
#
#         context['import_csv'] = import_csv
#
#         # Add ManufacturersForm to context
#         if self.request.user.manufacturers:
#             manufacturers_form = ManufacturersForm(instance=self.request.user.manufacturers)
#         else:
#             manufacturers_form = ManufacturersForm()
#
#         context['manufacturers_form'] = manufacturers_form
#         return context
#
#     def post(self, request, *args, **kwargs):
#         self.object = None
#         form = self.get_form()
#         manufacturers_form = ManufacturersForm(request.POST, request.FILES, instance=request.user.manufacturers)
#
#         if form.is_valid() and manufacturers_form.is_valid():
#             return self.form_valid(form, manufacturers_form)
#         else:
#             return self.form_invalid(form, manufacturers_form)
#
#     def form_valid(self, form, manufacturers_form):
#         csv_file = form.cleaned_data["csv_file"]
#
#         if not csv_file.name.endswith(".csv"):
#             messages.error(self.request, "Это не файл CSV.")
#             return self.form_invalid(form, manufacturers_form)
#
#         process_product_csv(csv_file, self.request)
#         messages.success(self.request, "Файл начал обработку в фоновом режиме.")
#
#         # Save the manufacturers form
#         manufacturers_form.save()
#
#         return super().form_valid(form)
#
#     def form_invalid(self, form, manufacturers_form):
#         context = self.get_context_data(form=form)
#         context['manufacturers_form'] = manufacturers_form
#         return self.render_to_response(context)


class OrderDetailView(DomainTemplateMixin, DetailView):
    model = SelectedProduct
    template_name = "order_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Определение, показывать ли форму отзывов
        context["show_reviews_form"] = not product.reviews
        context["show_reviews_form_update"] = bool(product.reviews)

        # Создание или обновление формы отзывов
        context["reviews_form"] = (
            ReviewsForm(instance=product.reviews) if product.reviews else ReviewsForm()
        )
        context["order"] = product.order_set.first()

        # Получение комментариев с предзагрузкой медиафайлов и пагинацией
        comments = (
            ProductComment.objects.filter(ticket=product)
            .select_related("ticket")
            .prefetch_related("commentmedia")
        )

        paginator = Paginator(comments, 10)
        page = self.request.GET.get("page")
        comments_paginated = paginator.get_page(page)

        # Передача необходимых данных в контекст
        context.update(
            {
                "ticket_comments": comments_paginated,
                "form": ProductCommentForm(),
                "ticket": product,
                "paginator": paginator,
                "page_obj": comments_paginated,
            }
        )

        # Получение данных SEO, если они существуют
        seo_data = Seo.objects.filter(pagetype=6).first()
        if seo_data:
            context.update(
                {
                    "seo_previev": seo_data.previev,
                    "seo_title": seo_data.title,
                    "seo_description": seo_data.metadescription,
                    "seo_propertytitle": seo_data.propertytitle,
                    "seo_propertydescription": seo_data.propertydescription,
                }
            )
        else:
            context.update(
                {
                    "seo_previev": None,
                    "seo_title": None,
                    "seo_description": None,
                    "seo_propertytitle": None,
                    "seo_propertydescription": None,
                }
            )

        return context

    def get_queryset(self):
        current_domain = self.request.get_host()
        filtered_products = Products.objects.filter(site__domain=current_domain)
        # Фильтруем SelectedProduct по товарам из filtered_products
        queryset = SelectedProduct.objects.filter(product__in=filtered_products)
        return queryset


class ProductCommentCreateView(CreateView):
    model = ProductComment
    form_class = ProductCommentForm

    @transaction.atomic
    def form_valid(self, form):
        ticket_id = self.kwargs["ticket_id"]
        ticket = get_object_or_404(SelectedProduct, id=ticket_id)
        comment = form.save(commit=False)
        comment.ticket = ticket
        comment.author = self.request.user
        comment.save()

        files = self.request.FILES.getlist("files")
        for file in files:
            ProductCommentMedia.objects.create(comment=comment, file=file)

        return JsonResponse(
            {
                "status": "success",
                "comment": {
                    "id": comment.id,
                    "author": comment.author.username,
                    "content": comment.content,
                    "date": comment.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "files": [
                        {"name": commentmedia.file.name, "url": commentmedia.file.url}
                        for commentmedia in comment.commentmedia.all()
                    ],
                },
            }
        )

    def form_invalid(self, form):
        print(form.errors)  # Для отладки
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


class ManufacturerReviewsListView(DomainTemplateMixin, ListView):
    model = Reviews
    template_name = "manufacturer_reviews.html"
    context_object_name = "reviews"
    paginate_by = 10

    def get_queryset(self):
        manufacturer = get_object_or_404(Manufacturers, profile=self.request.user)

        return Reviews.objects.filter(product__manufacturers=manufacturer)


class ManufacturerOrderListView(DomainTemplateMixin, ListView):
    model = Order
    template_name = "manufacturer_order.html"
    context_object_name = "orders"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Пожалуйста, войдите в систему.")
            return redirect(reverse("webmain:login"))

        if (
            not hasattr(request.user, "manufacturers")
            or request.user.manufacturers is None
        ):
            messages.error(request, "У вас нет доступа к этой странице.")
            return redirect(reverse("webmain:home"))

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Order.objects.all()
        logger.debug(f"Initial queryset count: {queryset.count()}")

        manufacturer = getattr(self.request.user, "manufacturers", None)
        logger.debug(f"Current manufacturer: {manufacturer}")

        if manufacturer:
            manufacturer_products = Products.objects.filter(manufacturers=manufacturer)
            logger.debug(
                f"Manufacturer products count: {manufacturer_products.count()}"
            )

            queryset = (
                queryset.filter(selectedproduct__product__in=manufacturer_products)
                .distinct()
                .order_by("-created_timestamp")
            )
            logger.debug(
                f"Queryset count after manufacturer filter: {queryset.count()}"
            )
        else:
            logger.warning("No manufacturer found for the current user")
            queryset = Order.objects.none()

        # Apply filters based on GET parameters
        filters = {}

        type = self.request.GET.get("type")
        if type and type != "all":
            filters["type"] = type

        status = self.request.GET.get("status")
        if status and status != "all":
            filters["status"] = status

        phone_number = self.request.GET.get("phone_number")
        if phone_number:
            filters["phone_number__icontains"] = phone_number

        customer_email = self.request.GET.get("customer_email")
        if customer_email:
            filters["customer_email__icontains"] = customer_email

        delivery_address = self.request.GET.get("delivery_address")
        if delivery_address:
            filters["delivery_address__icontains"] = delivery_address

        amount_min = self.request.GET.get("amount_min")
        amount_max = self.request.GET.get("amount_max")
        if amount_min and amount_max:
            filters["amount__range"] = (amount_min, amount_max)
        elif amount_min:
            filters["amount__gte"] = amount_min
        elif amount_max:
            filters["amount__lte"] = amount_max

        created_from = self.request.GET.get("created_from")
        created_to = self.request.GET.get("created_to")
        if created_from and created_to:
            filters["created_timestamp__range"] = (
                datetime.strptime(created_from, "%Y-%m-%d"),
                datetime.strptime(created_to, "%Y-%m-%d"),
            )
        elif created_from:
            filters["created_timestamp__gte"] = datetime.strptime(
                created_from, "%Y-%m-%d"
            )
        elif created_to:
            filters["created_timestamp__lte"] = datetime.strptime(
                created_to, "%Y-%m-%d"
            )

        queryset = queryset.filter(**filters)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["manufacturer"] = getattr(self.request.user, "manufacturers", None)
        context["current_filters"] = self.request.GET
        context["payment_types"] = [("all", "Все типы")] + list(Order.PAYMENT_TYPE)
        context["status_choices"] = [("all", "Все статусы")] + list(Order.STATUS)
        return context


class OrderUpdateView(DomainTemplateMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "order_update"
    context_object_name = "order"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Пожалуйста, войдите в систему.")
            return redirect("webmain:login")

        if (
            not hasattr(request.user, "manufacturers")
            or request.user.manufacturers is None
        ):
            messages.error(request, "У вас нет доступа к этой странице.")
            return redirect("webmain:home")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        manufacturer = getattr(self.request.user, "manufacturers", None)

        if manufacturer:
            manufacturer_products = Products.objects.filter(manufacturers=manufacturer)

            if manufacturer_products.exists():
                queryset = Order.objects.filter(
                    selectedproduct__product__in=manufacturer_products
                ).distinct()
                return queryset
            else:
                return Order.objects.none()
        else:
            return Order.objects.none()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        pk = self.kwargs.get("pk")
        order = get_object_or_404(queryset, pk=pk)
        return order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["selectedproduct_formset"] = SelectedProductFormSet(
                self.request.POST, queryset=self.object.selectedproduct.all()
            )
        else:
            context["selectedproduct_formset"] = SelectedProductFormSet(
                queryset=self.object.selectedproduct.all()
            )
        context["manufacturer"] = getattr(self.request.user, "manufacturers", None)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["selectedproduct_formset"]
        if formset.is_valid():
            self.object = form.save()
            selected_products = formset.cleaned_data

            # Очистка текущих связей
            self.object.selectedproduct.clear()

            for product_form in formset:
                if product_form.cleaned_data and not product_form.cleaned_data.get(
                    "DELETE", False
                ):
                    selected_product = product_form.save()
                    self.object.selectedproduct.add(selected_product)

            messages.success(self.request, "Заказ успешно обновлен.")
            return redirect(self.get_success_url())
        else:
            messages.error(self.request, "Ошибка при обновлении заказа.")
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse("shop:manufacturerorder")


# Applying CSRF exemption if needed (use cautiously, depending on context)
@method_decorator(csrf_exempt, name="dispatch")
class AddFaqView(DomainTemplateMixin, View):
    def post(self, request, *args, **kwargs):
        product_id = request.POST.get("product_id")
        question = request.POST.get("question")

        if not product_id or not question:
            return JsonResponse(
                {"success": False, "message": "Product ID and question are required"}
            )

        try:
            product = Products.objects.get(id=product_id)

            new_faq = FaqsProducts.objects.create(
                product=product,
                user=request.user,
                question=question,
                create=timezone.now(),  # Ensure correct timestamp
            )

            # Format the creation date to the desired format
            formatted_date = date_format(
                new_faq.create, format="j E Y, H:i"
            )  # Example: 6 мая 2024 г. 6:56

            new_faq_data = {
                "user_name": request.user.username,
                "avatar": request.user.avatar.url,
                "created": formatted_date,
                "question": new_faq.question,
            }

            return JsonResponse({"success": True, "new_faq": new_faq_data})
        except Products.DoesNotExist:
            return JsonResponse({"success": False, "message": "Product not found"})

        return JsonResponse({"success": False, "message": "Invalid request method"})


logger = logging.getLogger(__name__)
def _qd_all(qd):
    return {k: qd.getlist(k) for k in qd.keys()}

@method_decorator(csrf_exempt, name="dispatch")
class SubmitReviewView(View):
    def post(self, request, *args, **kwargs):
        # ... (твои print'ы как раньше)

        if not request.user.is_authenticated:
            return JsonResponse({"status":"error","message":"User not authenticated"}, status=403)

        product_id = request.POST.get("product")

        form = ReviewsForm(request.POST)  # без request.FILES — файлы сохраняем вручную
        if not form.is_valid():
            return JsonResponse({"status":"error","errors":form.errors}, status=400)

        try:
            with transaction.atomic():
                # 1) Зарезервируем строку SelectedProduct, чтобы убрать гонки привязки
                selected_product, _ = SelectedProduct.objects.select_for_update().get_or_create(
                    user=request.user, product_id=product_id,
                    defaults={"status": 2}
                )

                # 2) Создаём или обновляем ОТЗЫВ (идемпотентно)
                review, created = Reviews.objects.update_or_create(
                    author=request.user,
                    product_id=product_id,
                    defaults={
                        "text": form.cleaned_data["text"],
                        "starvalue": form.cleaned_data["starvalue"],
                        # другие поля, если появятся
                    },
                )

                # 3) Привяжем к SelectedProduct
                selected_product.review = review
                selected_product.reviews = True
                selected_product.save(update_fields=["review", "reviews"])

        except IntegrityError:
            # На случай, если параллельный запрос всё-таки опередил (уникальный индекс сработал)
            review = Reviews.objects.get(author=request.user, product_id=product_id)
            created = False

        # 4) Сохраняем изображения (можно заменить на «очистить и перезаписать», см. ниже)
        saved_urls = []
        for f in request.FILES.getlist("images"):
            img = ReviewImage.objects.create(review=review, image=f)
            saved_urls.append(img.image.url)

        return JsonResponse({
            "status": "success",
            "review": {
                "text": review.text,
                "author": review.author.username,
                "author_avatar": getattr(review.author, "avatar", None).url
                    if getattr(review.author, "avatar", None) else "",
                "starvalue": review.starvalue,
                "images": saved_urls or [ri.image.url for ri in review.images.all()],
                "created": created,  # True если был создан, False если обновили
            },
        })

    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(["POST"])




class AddToCartView(View):
    def post(self, request):
        product_id = request.POST.get("product_id")
        variation_slug = request.POST.get("variation_slug")
        position_type = request.POST.get("position_type")
        quantity = int(request.POST.get("quantity", 1))
        print(request.POST)
        if not product_id or quantity <= 0:
            return JsonResponse(
                {"success": False, "message": "Invalid data"}, status=400
            )

        # Проверяем, существует ли продукт
        try:
            product = Products.objects.get(id=product_id)
        except Products.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Product not found"}, status=404
            )

        if quantity > product.quantity:
            return JsonResponse(
                {"success": False, "message": "Количество товара указано не верно"},
                status=400,
            )

        # Убедимся, что у сессии есть session_key
        session_key = request.session.session_key
        if not session_key:
            request.session.create()  # Создаем session_key
            session_key = request.session.session_key

        # Устанавливаем user если он аутентифицирован
        user = request.user if request.user.is_authenticated else None
        if variation_slug:
            variety = get_object_or_404(ProductsVariable, slug=variation_slug)
            selected_product, sp_created = SelectedProduct.objects.get_or_create(
                product=product,
                session_key=session_key,
                status=1,
                defaults={"user": user},
                variety=variety,
            )
        else:
            variety = None
            # Создаем или получаем SelectedProduct
            selected_product, sp_created = SelectedProduct.objects.get_or_create(
                product=product,
                session_key=session_key,
                status=1,
                defaults={
                    "user": user,
                    "variety": variety,
                    "quantity": Decimal("0"),
                    "amount": Decimal("0"),
                },
            )

        if not sp_created and selected_product.user is None and user is not None:
            selected_product.user = user
            selected_product.save()

        # Обновляем количество и сумму
        selected_product.quantity += quantity
        selected_product.save()

        current_domain = request.get_host()
        current_site = Site.objects.get(domain=current_domain)
        session = request.session

        # Логирование для отладки
        print(f"Current site ID: {current_site.id}, Domain: {current_site.domain}")

        # Сохраняем сессию если нужно
        if not session.session_key:
            session.save()

        # Генерим browser_key
        client_ip, _ = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = session.session_key

        try:
            if request.user.is_authenticated:
                # Ищем корзину пользователя для текущего сайта
                cart = Cart.objects.get(user=request.user, site=current_site)
            else:
                # Ищем корзину анонима для текущего сайта
                cart = Cart.objects.get(
                    browser_key=browser_key, session_key=session_key, site=current_site
                )
        except Cart.DoesNotExist:
            # Создаем новую корзину с привязкой к сайту
            cart = Cart.objects.create(
                user=request.user if request.user.is_authenticated else None,
                browser_key=browser_key,
                session_key=session_key,
                amount=Decimal("0"),
            )
            cart.site.add(current_site)

        # Добавляем SelectedProduct в корзин
        if not cart.selectedproduct.filter(id=selected_product.id).exists():
            cart.selectedproduct.add(selected_product)

        valute = Valute.objects.get(id=1)
        relationship = valute.relationship

        if variation_slug:
            variety = get_object_or_404(ProductsVariable, slug=variation_slug)
            price = variety.price
            product_valute = variety.products.valute
            if not product_valute:
                product_valute = (
                    Valute.objects.first()
                )  # берем первую валюту, если нет у продукта
            if product_valute != valute:
                new_price = price * product_valute.relationship
            else:
                new_price = price
            cart.amount += new_price * quantity
            cart.save()

        else:
            price = product.price
            if product.valute != valute:
                new_price = price * relationship
            else:
                new_price = price
            cart.amount += new_price * Decimal(quantity)
            cart.save()
        if position_type == "header":
            previous_page = request.META.get("HTTP_REFERER")
            return redirect(previous_page)
        else:
            cart.refresh_from_db()
            selected_product.refresh_from_db()
            return JsonResponse(
                {
                    "success": True,
                    "cart_amount": cart.amount,
                    "quantity": selected_product.quantity,
                    "message": "Товар добавлен в корзину",
                },
                status=201,
            )


class CartItemCountView(DomainTemplateMixin, View):
    def get(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        client_ip, _ = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=request.user
            )
        else:
            # Combine session_key and browser_key to identify the cart
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )

        cart_item_count = cart.selectedproduct.count()

        return JsonResponse({"cart_item_count": cart_item_count})


class CartItemsView(DomainTemplateMixin, View):
    def get(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        client_ip, _ = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=request.user
            )
        else:
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )

        cart_products = []
        for selected_product in cart.selectedproduct.all():
            cart_products.append(
                {
                    "name": selected_product.product.name,
                    "description": selected_product.product.description,
                    "image_url": selected_product.product.image.url,
                    "price": selected_product.product.price,
                    "quantity": selected_product.quantity,
                    "amount": selected_product.amount,
                    "slug": selected_product.product.slug,
                }
            )

        # Добавляем данные корзины в ответ
        return JsonResponse(
            {
                "cart_products": cart_products,
                "cart_total": cart.get_cart_total(),
                "cart_empty": cart.selectedproduct.count()
                == 0,  # Используем count вместо проверки на empty
            }
        )


class CartMixin:
    """Общая логика для работы с корзиной"""

    def get_cart(self, request):
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        client_ip, _ = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()

        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=request.user
            )
        else:
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )
        return cart

    def json_response(self, cart):
        return {
            "success": True,
            "new_total": cart.get_formatted_total(),
            "cart_empty": cart.selectedproduct.count() == 0,
            "cart_total": cart.get_formatted_total(),
        }


class RemoveFromCartView(CartMixin, View):
    def post(self, request, product_slug):
        cart = self.get_cart(request)
        try:
            item = cart.selectedproduct.get(product__slug=product_slug)
            item.delete()
            return JsonResponse(self.json_response(cart))  # Исправлено здесь
        except SelectedProduct.DoesNotExist:
            return JsonResponse({"success": False}, status=404)


@method_decorator(require_http_methods(["POST"]), name="dispatch")
class UpdateCartItemView(CartMixin, View):
    def post(self, request, product_slug):
        cart = self.get_cart(request)
        try:
            item = cart.selectedproduct.get(product__slug=product_slug)
            data = json.loads(request.body)
            action = data.get("action")

            if action == "increment":
                item.quantity += 1
            elif action == "decrement":
                item.quantity = max(1, item.quantity - 1)

            item.save()

            # Формируем базовый ответ и добавляем новое поле
            response_data = self.json_response(cart)
            response_data["new_quantity"] = item.quantity
            return JsonResponse(response_data)

        except SelectedProduct.DoesNotExist:
            return JsonResponse({"success": False}, status=404)


from django.utils import timezone


class ApplicationCreateView(View):
    """View для обработки создания Applications через AJAX-запрос"""

    def post(self, request):
        data = request.POST
        email = data["email"]
        phone = data["phone"]
        content = data["content"]
        product_id = data["product_id"]

        application = Applications(
            type=1,
            products_id=product_id,
            email=email,
            phone=phone,
            content=content,
            create=timezone.now(),
            user=request.user if request.user.is_authenticated else None,
        )

        application.save()

        return JsonResponse({"status": "success", "message": "Вы оставили заявку"})


class BookmarkAddView(DomainTemplateMixin, View):
    """View для добавления продукта в закладки"""

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "Not authenticated"}, status=401
            )

        product_id = request.POST.get("product_id")
        product = get_object_or_404(Products, id=product_id)
        person = request.user

        if product in person.bookmark.all():
            return JsonResponse(
                {"status": "error", "message": "Already bookmarked"}, status=400
            )

        person.bookmark.add(product)

        return JsonResponse(
            {
                "status": "success",
                "message": "Product added to bookmarks",
                "count": person.bookmark.count(),
            }
        )


class BookmarkDeleteView(DomainTemplateMixin, View):
    """View для удаления продукта из закладок"""

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse(
                {"status": "error", "message": "User not authenticated"}, status=401
            )

        product_id = request.POST.get("product_id")
        product = get_object_or_404(Products, id=product_id)
        person = get_object_or_404(Profile, id=request.user.id)

        if product not in person.bookmark.all():
            return JsonResponse(
                {"status": "error", "message": "Product not in bookmarks"}, status=404
            )

        person.bookmark.remove(product)

        return JsonResponse(
            {
                "status": "success",
                "message": "Product removed from bookmarks",
                "count": person.bookmark.count(),
            }
        )


class MyCartView(DomainTemplateMixin, DetailView):
    model = Cart
    template_name = "cart.html"
    context_object_name = "cart"

    def get_object(self):
        user = self.request.user

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=self.request.user
            )
        else:
            # Combine session_key and browser_key to identify the cart
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )  # Получаем корзину по session_key

        return cart

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.get_object()  # Корзина для текущего пользователя или сессии
        context["cart"] = cart  # Передаем корзину в контекст
        context["valute"] = cart.valute  # Передаем корзину в контекст

        products = list(cart.selectedproduct.all())
        product_count = cart.selectedproduct.count()
        print(
            f"Корзина через all: {cart}, товары: {list(cart.selectedproduct.all())}"
        )  # отладка

        print(
            f"Корзина: {cart}, товары: {products}, количество товаров: {product_count}"
        )  # отладка

        context["product_count"] = product_count

        # Добавляем информацию о закладках, если пользователь авторизован
        if self.request.user.is_authenticated:
            user = self.request.user
            person = get_object_or_404(Profile, id=user.id)
            bookmarked_products = (
                person.bookmark.all()
            )  # Получаем все закладки пользователя
            context["is_bookmarked"] = bookmarked_products

        return context

    def get_queryset(self):
        current_domain = self.request.get_host()
        filtered_products = Products.objects.filter(site__domain=current_domain)
        # Фильтруем SelectedProduct по товарам из filtered_products
        queryset = SelectedProduct.objects.filter(product__in=filtered_products)
        return queryset


class DeleteSelectedProductView(View):
    def post(self, request):
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=self.request.user
            )
        else:
            client_ip, _ = get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            browser_key = hashlib.md5(
                (client_ip + user_agent).encode("utf-8")
            ).hexdigest()
            session_key = request.session.session_key
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )

        if not cart:
            return JsonResponse(
                {"success": False, "message": "Корзина не найдена"}, status=400
            )

        selected_product_id = request.POST.get("selected_product_id")
        if not selected_product_id:
            return JsonResponse(
                {"success": False, "message": "ID продукта не передан"}, status=400
            )

        try:
            selected_product = SelectedProduct.objects.get(id=selected_product_id)
        except SelectedProduct.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Продукт не найден"}, status=404
            )

        if selected_product not in cart.selectedproduct.all():
            return JsonResponse(
                {"success": False, "message": "Продукт не в корзине"}, status=400
            )

        selected_product.delete()
        cart.amount = sum(sp.amount for sp in cart.selectedproduct.all())
        cart.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Продукт удалён",
                "cart_total": str(cart.amount),
            }
        )


def update_cart_amount(cart):
    # Пересчитываем общую сумму корзины
    total_amount = sum(sp.amount for sp in cart.selectedproduct.all())
    cart.amount = total_amount
    cart.save()

@method_decorator(csrf_exempt, name="dispatch")
class UpdateProductQuantityView(DomainTemplateMixin, View):
    def post(self, request, product_id):
        selected_product = SelectedProduct.objects.get(id=product_id)
        data = json.loads(request.body)

        new_quantity = data.get("quantity")
        new_amount = data.get("amount")
        print(new_amount)
        print(new_quantity)
        user = self.request.user

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=self.request.user
            )
        else:
            # Combine session_key and browser_key to identify the cart
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )  # Получаем корзину по session_key

        cart_valute = cart.valute

        prod_valute = Valute.objects.get(id=selected_product.product.valute.id)

        if cart_valute != prod_valute:
            conversion_rate = Decimal(prod_valute.relationship) / Decimal(
                cart_valute.relationship
            )
            new_price = Decimal(new_amount) * conversion_rate
            if cart_valute.allowance != 0:
                difference = new_price * (Decimal(cart_valute.allowance) / Decimal(100))
                new_price += difference
            new_price = new_price.quantize(
                Decimal("1.00"), rounding=ROUND_DOWN
            )  # Округление до 2-х знаков после запятой
        else:
            new_price = new_amount

        if new_quantity is not None and new_quantity > 0:
            # Обновляем `SelectedProduct.quantity` и `SelectedProduct.amount`
            selected_product.quantity = new_quantity
            selected_product.amount = new_price
            selected_product.save()

            # Обновляем `Cart.amount`
            cart = Cart.objects.filter(
                selectedproduct=selected_product
            ).first()  # Предполагаем, что продукт связан с одной корзиной
            if cart:
                update_cart_amount(cart)  # Пересчитываем общую сумму корзины

            return JsonResponse(
                {
                    "success": True,
                    "quantity": selected_product.quantity,
                    "amount": selected_product.amount,
                    "cart_amount": cart.amount,  # Возвращаем обновленную сумму корзины
                }
            )
        else:
            return JsonResponse(
                {"success": False, "message": "Invalid quantity or amount"}, status=400
            )

class PurchasedProductListView(DomainTemplateMixin, ListView):
    model = PurchasedProduct
    template_name = "purchased_products_list.html"
    context_object_name = "products"
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        current_domain = self.request.get_host()
        current_site = Site.objects.get(domain=current_domain)
        return Order.objects.filter(user=user, site=current_site).order_by(
            "-created_timestamp"
        )  # Возвращаем заказы текущего пользователя

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_domain = self.request.get_host()
        user = self.request.user


        try:
            seo_data = Seo.objects.get(
                pagetype=5, site__domain=current_domain
            )  # Фильтруем по домену
            context["seo_previev"] = seo_data.previev
            context["seo_title"] = seo_data.title

            context["seo_propertytitle"] = seo_data.propertytitle
            context["seo_propertydescription"] = seo_data.propertydescription
        except Seo.DoesNotExist:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None

        now = timezone.now()
        active_promotions = PersonalPromotion.objects.filter(
            user=user,
            is_active=True,
        ).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=now)
        )


        context["personal_promotions"] = [
            list(group) for group in itertools.zip_longest(*[iter(active_promotions)] * 3)
        ]

        return context


class MyOrderView(DomainTemplateMixin, ListView):
    """Страницы"""

    model = Order
    template_name = "order.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        current_domain = self.request.get_host()
        current_site = Site.objects.get(domain=current_domain)
        return Order.objects.filter(user=user, site=current_site).order_by(
            "-created_timestamp"
        )  # Возвращаем заказы текущего пользователя

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_domain = self.request.get_host()
        user = self.request.user

        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key
        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                site__domain=self.request.get_host(), user=self.request.user
            )
        else:
            # Combine session_key and browser_key to identify the cart
            cart, created = Cart.objects.get_or_create(
                browser_key=browser_key,
                site__domain=self.request.get_host(),
                defaults={"session_key": session_key},
            )  # Получаем корзину по session_key

        cart_valute = cart.valute
        context["valute"] = cart_valute
        try:
            seo_data = Seo.objects.get(
                pagetype=5, site__domain=current_domain
            )  # Фильтруем по домену
            context["seo_previev"] = seo_data.previev
            context["seo_title"] = seo_data.title

            context["seo_propertytitle"] = seo_data.propertytitle
            context["seo_propertydescription"] = seo_data.propertydescription
        except Seo.DoesNotExist:
            context["seo_previev"] = None
            context["seo_title"] = None
            context["seo_description"] = None
            context["seo_propertytitle"] = None
            context["seo_propertydescription"] = None

        return context


class BookmarkListView(DomainTemplateMixin, ListView):
    """Представление для вывода закладок текущего пользователя"""

    model = Profile
    template_name = "bookmarks.html"
    context_object_name = "is_bookmarked"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        current_domain = self.request.get_host()

        return user.bookmark.filter(site__domain__in=[current_domain]).distinct()



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Текущий пользователь
        user = self.request.user
        # Заявки пользователя
        # user_applications = Applications.objects.filter(user=user)
        # Продукты, которые есть в заявках
        # applied_product_ids = list(user_applications.values_list('products', flat=True))
        # applied_products = Products.objects.filter(id__in=applied_product_ids)
        current_site = get_current_site(self.request)
        # Убедитесь, что данные передаются в контекст
        # context['application_exists'] = applied_products
        # конвертация валют
        client_ip, _ = get_client_ip(self.request)
        user_agent = self.request.META.get("HTTP_USER_AGENT", "")
        browser_key = hashlib.md5((client_ip + user_agent).encode("utf-8")).hexdigest()
        session_key = self.request.session.session_key

        # Ищем корзину по session_key и site, без создания новой
        cart = (
            Cart.objects.filter(session_key=session_key, site=current_site).first()
            or Cart.objects.filter(browser_key=browser_key, site=current_site).first()
        )

        # Если корзина найдена, добавляем её валюту в контекст
        if cart:
            context["valute"] = cart.valute
        else:
            context["cart_error"] = "Корзина не найдена"

        # # Получение данных SEO для страницы
        # try:
        #     seo_data = Seo.objects.get(pagetype=7)
        #     context.update({
        #         'seo_previev': seo_data.previev,
        #         'seo_title': seo_data.title,
        #         'seo_description': seo_data.description,
        #         'seo_propertytitle': seo_data.propertytitle,
        #         'seo_propertydescription': seo_data.propertydescription,
        #     })
        # except Seo.DoesNotExist:
        #     context.update({
        #         'seo_previev': None,
        #         'seo_title': None,
        #         'seo_description': None,
        #         'seo_propertytitle': None,
        #         'seo_propertydescription': None,
        #     })

        return context


from django.views import View
from .forms import UpdateCartCurrencyForm, ManufacturersForm, CSVUploadForm
from .models import Cart, Valute, StockAvailability, Storage


class UpdateCartCurrencyView(View):
    def post(self, request, *args, **kwargs):
        form = UpdateCartCurrencyForm(request.POST)
        if form.is_valid():
            cart = None
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.filter(session_key=session_key).first()
            if not cart and request.user.is_authenticated:
                cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart.valute = form.cleaned_data["valute"]
                cart.save()
                return JsonResponse({"success": True})
            else:
                return JsonResponse(
                    {"success": False, "message": "Корзина не найдена."}
                )
        else:
            return JsonResponse({"success": False, "message": "Ошибка в форме."})


class UserUploadCSVView(DomainTemplateMixin, FormView):
    template_name = "upload_csv.html"
    form_class = CSVUploadForm
    success_url = "/shop_edit/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pagination setup
        import_csv_list = ImportCsv.objects.all()
        paginator = Paginator(import_csv_list, 10)
        page = self.request.GET.get("page")

        try:
            import_csv = paginator.page(page)
        except PageNotAnInteger:
            import_csv = paginator.page(1)
        except EmptyPage:
            import_csv = paginator.page(paginator.num_pages)

        context["import_csv"] = import_csv

        # Add ManufacturersForm to context
        if self.request.user.manufacturers:
            manufacturers_form = ManufacturersForm(
                instance=self.request.user.manufacturers
            )
        else:
            manufacturers_form = ManufacturersForm()

        context["manufacturers_form"] = manufacturers_form
        return context

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        manufacturers_form = ManufacturersForm(
            request.POST, request.FILES, instance=request.user.manufacturers
        )

        if form.is_valid() and manufacturers_form.is_valid():
            return self.form_valid(form, manufacturers_form)
        else:
            return self.form_invalid(form, manufacturers_form)

    def form_valid(self, form, manufacturers_form):
        csv_file = form.cleaned_data["csv_file"]

        if not csv_file.name.endswith(".csv"):
            messages.error(self.request, "Это не файл CSV.")
            return self.form_invalid(form, manufacturers_form)

        # process_product_csv(csv_file, self.request)
        messages.success(self.request, "Файл начал обработку в фоновом режиме.")

        # Save the manufacturers form
        manufacturers_form.save()

        return super().form_valid(form)

    def form_invalid(self, form, manufacturers_form):
        context = self.get_context_data(form=form)
        context["manufacturers_form"] = manufacturers_form
        return self.render_to_response(context)
