# compare/utils.py
from django.contrib.sites.shortcuts import get_current_site
from .models import CompareList, CompareItem
from shop.models import Products

MAX_COMPARE = 4
SESSION_KEY = "compare_ids"

def _get_session_ids(request):
    ids = request.session.get(SESSION_KEY, [])
    # нормализуем к строкам (UUID to str)
    request.session[SESSION_KEY] = [str(x) for x in ids]
    return request.session[SESSION_KEY]

def _set_session_ids(request, ids):
    request.session[SESSION_KEY] = [str(x) for x in ids]
    request.session.modified = True

def get_or_create_compare_list(request):
    site = get_current_site(request)
    if request.user.is_authenticated:
        compare, _ = CompareList.objects.get_or_create(user=request.user, site=site)
        return compare
    # гости — временная оболочка
    session_key = request.session.session_key or request.session.save() or request.session.session_key
    compare, _ = CompareList.objects.get_or_create(session_key=session_key, site=site)
    return compare

def merge_session_to_user(request):
    """При логине: переложить из сессии в БД, с сохранением лимита."""
    if not request.user.is_authenticated:
        return
    ids = _get_session_ids(request)
    if not ids:
        return
    compare = get_or_create_compare_list(request)
    # сначала добавим существующие id в compare
    existing_ids = set(compare.items.values_list("product_id", flat=True))
    for pid in ids:
        if len(existing_ids) >= MAX_COMPARE:
            break
        try:
            product = Products.objects.get(pk=pid)
        except Products.DoesNotExist:
            continue
        if product.pk in existing_ids:
            continue
        CompareItem.objects.create(compare=compare, product=product)
        existing_ids.add(product.pk)
    # очистим сессию
    _set_session_ids(request, [])

def add_to_compare(request, product_id):
    if request.user.is_authenticated:
        compare = get_or_create_compare_list(request)
        if compare.items.count() >= MAX_COMPARE:
            return False, "Максимум товаров для сравнения: %d" % MAX_COMPARE
        obj, created = CompareItem.objects.get_or_create(compare=compare, product_id=product_id)
        return True, "Добавлено" if created else "Уже в сравнении"
    # гости — сессия
    ids = _get_session_ids(request)
    if str(product_id) in ids:
        return True, "Уже в сравнении"
    if len(ids) >= MAX_COMPARE:
        return False, "Максимум товаров для сравнения: %d" % MAX_COMPARE
    ids.append(str(product_id))
    _set_session_ids(request, ids)
    return True, "Добавлено"

def remove_from_compare(request, product_id):
    if request.user.is_authenticated:
        compare = get_or_create_compare_list(request)
        CompareItem.objects.filter(compare=compare, product_id=product_id).delete()
    else:
        ids = _get_session_ids(request)
        ids = [x for x in ids if x != str(product_id)]
        _set_session_ids(request, ids)
    return True

def get_compare_products(request):
    """Вернуть QuerySet выбранных товаров в порядке добавления."""
    if request.user.is_authenticated:
        compare = get_or_create_compare_list(request)
        ids = list(compare.items.order_by("added_at").values_list("product_id", flat=True))
    else:
        ids = _get_session_ids(request)
    qs = Products.objects.filter(pk__in=ids).select_related("brand", "valute").prefetch_related(
        "manufacturers", "atribute"
    )
    # сохранить порядок ids
    products_by_id = {str(p.pk): p for p in qs}
    ordered = [products_by_id.get(str(pid)) for pid in ids]
    return [p for p in ordered if p]
