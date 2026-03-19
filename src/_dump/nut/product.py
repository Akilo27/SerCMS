# -*- coding: utf-8 -*-
"""
Фундучок: парсинг нескольких категорий.
1) Собираем ссылки товаров из каждой категории (?page=N)
2) Обходим карточки и вытягиваем подробные данные

Ввод категорий:
  - Либо прописать в CATEGORIES ниже
  - Либо создать рядом файл categories.txt (по одной ссылке на строку)
    Пример:
      https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/orehi/
      https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/suhofrukty/

Выход:
  - funduchok_products.json   (полные данные)
  - funduchok_products.csv    (базовые поля по товарам, есть column source_categories)
  - funduchok_variants.csv    (варианты / фасовки)
"""

import csv
import json
import re
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# ---------- НАСТРОЙКИ ----------
# Вариант 1: список категорий здесь
CATEGORIES = [
    # Примеры:
    "https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/orehi/",
    "https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/suhofrukty/",
    "https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/sladosti/",
    "https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/semechki/",
    "https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/specii-i-prjanosti/",
    "https://xn--d1amhfwcd2a.xn--p1ai/katalog-tovarov/chaj/",
]

MAX_PAGES = 50           # максимум страниц пагинации на одну категорию
REQUEST_DELAY = 0.6      # задержка между запросами, сек
TIMEOUT = 30

OUT_JSON = Path("funduchok_products.json")
OUT_CSV_PRODUCTS = Path("funduchok_products.csv")
OUT_CSV_VARIANTS = Path("funduchok_variants.csv")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://xn--d1amhfwcd2a.xn--p1ai/",
}

session = requests.Session()
session.headers.update(HEADERS)


# ---------- ВСПОМОГАТЕЛЬНЫЕ ----------

def ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else url + "/"

def soupify(html: str) -> BeautifulSoup:
    """Безопасно создаём BS: lxml если есть, иначе html.parser."""
    try:
        import lxml  # noqa: F401
        parser = "lxml"
    except Exception:
        parser = "html.parser"
    return BeautifulSoup(html, parser)

def get(url: str) -> requests.Response:
    """GET с несколькими попытками и таймаутом."""
    last_exc = None
    for attempt in range(3):
        try:
            resp = session.get(url, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp
        except Exception as e:
            last_exc = e
        time.sleep(0.5 + attempt)
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Failed GET {url}")

def text_to_int(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None

def clean_url(u: Optional[str]) -> Optional[str]:
    """
    Чистим кривые URL вида:
      "https://xn--...aihttps://520925.selcdn.ru/..."
    Берём последнюю валидную часть "https://...".
    """
    if not u:
        return u
    u = u.strip()
    parts = re.findall(r"https?://[^\s\"']+", u)
    if parts:
        return parts[-1]
    return u

def absolutize(base_url: str, href: Optional[str]) -> Optional[str]:
    """
    Склеиваем ссылку к КОРНЮ домена (а не к хвосту пути),
    чистим "https://...aihttps://..." и убираем повтор "/katalog-tovarov/".
    """
    if not href:
        return None

    # 1) чистим двойные https
    href = clean_url(href)

    # 2) абсолютная? — возвращаем как есть
    if re.match(r"^https?://", href, flags=re.I):
        full = href
    else:
        pr = urlparse(base_url)
        root = f"{pr.scheme}://{pr.netloc}"

        if href.startswith("//"):          # //cdn.example.com/...
            full = f"{pr.scheme}:{href}"
        elif href.startswith("/"):          # /katalog-tovarov/...
            full = f"{root}{href}"
        else:                               # katalog-tovarov/...
            full = f"{root}/{href}"

    # 3) нормализуем повторы .../katalog-tovarov/.../katalog-tovarov/...
    p = urlparse(full)
    path = p.path
    if path.count("/katalog-tovarov/") > 1:
        first = path.find("/katalog-tovarov/")
        path = path[first:]
        full = f"{p.scheme}://{p.netloc}{path}"

    return full

def availability_from_str(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.lower()
    if "instock" in s:
        return "in_stock"
    if "outofstock" in s:
        return "out_of_stock"
    return None


# ---------- ШАГ 1. СБОР ССЫЛОК ИЗ КАТЕГОРИИ ----------

def extract_product_links_from_category(html: str, base_url: str) -> List[str]:
    """
    Ищем ссылки товаров на категории:
      - <a href=".../katalog-tovarov/.../*.html">
    Берём относительные и абсолютные; фильтруем дубликаты.
    """
    links = set()
    soup = soupify(html)

    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("javascript:", "#")):
            continue
        full = absolutize(base_url, href)
        if not full:
            continue
        path = urlparse(full).path
        if "/katalog-tovarov/" in path and path.endswith(".html"):
            links.add(full)

    # Regex-фолбэк (на случай JS-генерации ссылок)
    if not links:
        for m in re.findall(r'href=[\'"]([^\'"]+/katalog-tovarov/[^\'"]+?\.html)[\'"]', html, flags=re.I):
            full = absolutize(base_url, m)
            if full:
                links.add(full)
        for m in re.findall(r'href=[\'"]([^\'"]+?\.html)[\'"]', html, flags=re.I):
            full = absolutize(base_url, m)
            if full and "/katalog-tovarov/" in urlparse(full).path:
                links.add(full)

    return sorted({u for u in links if u})

def iterate_category_pages(base_category_url: str, max_pages: int) -> List[str]:
    """
    Собираем ВСЕ ссылки товаров по страницам ?page=N,
    останавливаемся, если две страницы подряд не дали новых ссылок.
    """
    base_category_url = ensure_trailing_slash(base_category_url)
    page = 1
    seen = set()
    empty_streak = 0
    all_links: List[str] = []

    while page <= max_pages:
        url = base_category_url if page == 1 else f"{base_category_url}?page={page}"
        print(f"[Категория стр. {page}] {url}")
        resp = get(url)
        html = resp.text

        links = extract_product_links_from_category(html, base_category_url)
        # подстраховка нормализации
        links = [absolutize(base_category_url, u) for u in links]
        links = [u for u in links if u]

        new_links = [u for u in links if u not in seen]
        print(f"  найдено: {len(links)}, новых: {len(new_links)}")

        if not new_links:
            empty_streak += 1
        else:
            empty_streak = 0

        all_links.extend(new_links)
        seen.update(new_links)

        if empty_streak >= 2:
            print("  две страницы без новых ссылок — стоп пагинации")
            break

        page += 1
        time.sleep(REQUEST_DELAY)

    return all_links


# ---------- ШАГ 2. ПАРСИНГ КАРТОЧКИ ТОВАРА ----------

def parse_variants(soup: BeautifulSoup) -> List[Dict]:
    """
    Варианты фасовки (label.label--packaging-card):
      - input[name="options[packaging]"][data-price][value(вес)]
      - .old-price (старая цена)
      - data-discount-amount, data-bonus, data-option_name
    """
    variants = []
    for label in soup.select("label.label--packaging-card"):
        try:
            inp = label.select_one('input[type="radio"][name="options[packaging]"]')
            if not inp:
                continue

            weight_g = text_to_int(inp.get("value"))
            price = text_to_int(inp.get("data-price"))
            old_price_el = label.select_one(".old-price")
            old_price = text_to_int(old_price_el.get_text()) if old_price_el else None

            data_discount_amount = text_to_int(inp.get("data-discount-amount"))
            data_bonus = text_to_int(inp.get("data-bonus"))
            option_name = (inp.get("data-option_name") or "").strip() or None

            title = " ".join(label.get_text(" ", strip=True).split()) or None

            variants.append({
                "weight_g": weight_g,
                "price": price,
                "old_price": old_price,
                "data_discount_amount": data_discount_amount,
                "data_bonus": data_bonus,
                "option_name": option_name,
                "title": title,
            })
        except Exception as e:
            print(f"    [!] variant error: {e}")
    return variants

def parse_properties_table_strict(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Жёстко целимся в таб с id="profile":
      <div id="profile"> ... <table> ... </table> ... </div>
    """
    props: Dict[str, str] = {}
    profile = soup.find(id="profile")
    if not profile:
        return props
    table = profile.select_one(".text__container table") or profile.select_one("table")
    if not table:
        return props

    rows = table.select("tbody tr") or [tr for tr in table.select("tr") if not tr.find_parent("thead")]
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) >= 2:
            name = " ".join(tds[0].get_text(" ", strip=True).split())
            value = " ".join(tds[1].get_text(" ", strip=True).split())
            if name:
                props[name] = value

    for row in table.select('tr[itemprop="additionalProperty"]'):
        name_el = row.select_one('[itemprop="name"]')
        val_el  = row.select_one('[itemprop="value"]')
        name = name_el.get_text(" ", strip=True) if name_el else None
        value = val_el.get_text(" ", strip=True) if val_el else None
        if name and name not in props:
            props[name] = value or ""
    return props

def parse_gallery_images(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Коллекция картинок:
      <a data-fancybox="gallery" href="...big.jpg"><img ...></a>
    """
    imgs = []
    for a in soup.select('a[data-fancybox="gallery"][href]'):
        href = clean_url(a.get("href"))
        full = absolutize(base_url, href)
        if full and full not in imgs:
            imgs.append(full)

    for img in soup.select('.product__card__gallery img[src]'):
        full = absolutize(base_url, img.get("src"))
        if full and full not in imgs:
            imgs.append(full)

    return imgs

def parse_product_page(url: str) -> Dict:
    """Парсит карточку товара и возвращает словарь с данными."""
    r = get(url)
    soup = soupify(r.text)

    # ID из формы
    prod_id = None
    id_input = soup.select_one('.product__card__options__form input[name="id"]') \
               or soup.select_one('form.ms2_form input[name="id"]')
    if id_input and id_input.get("value"):
        prod_id = id_input["value"].strip()

    # SKU / Name / Category
    root = soup.select_one('[itemscope][itemtype*="Product"]') or soup

    sku = None
    sku_meta = root.select_one('meta[itemprop="sku"][content]') or soup.select_one('meta[itemprop="sku"][content]')
    if sku_meta:
        sku = sku_meta.get("content", "").strip() or None

    name = None
    h1 = soup.select_one('h1[itemprop="name"]') or root.select_one('[itemprop="name"]')
    if h1:
        name = h1.get_text(" ", strip=True)

    category = None
    category_el = soup.select_one('[itemprop="category"]')
    if category_el:
        category = category_el.get_text(" ", strip=True)

    # Цена/валюта/срок/наличие
    base_price = None
    price_meta = soup.select_one('meta[itemprop="price"][content]')
    if price_meta:
        base_price = text_to_int(price_meta.get("content"))

    currency = "RUB"
    cur_meta = soup.select_one('meta[itemprop="priceCurrency"][content]')
    if cur_meta:
        currency = (cur_meta.get("content") or "RUB").strip()

    price_valid_until = None
    pvu_meta = soup.select_one('meta[itemprop="priceValidUntil"][content]')
    if pvu_meta:
        price_valid_until = pvu_meta.get("content") or None

    availability = None
    av_el = soup.select_one('[itemprop="availability"]')
    if av_el:
        href = av_el.get("href") or av_el.get("content") or av_el.get_text(strip=True)
        availability = availability_from_str(href)

    # Изображения
    main_image = None
    img_meta = soup.select_one('meta[itemprop="image"][content]')
    if img_meta and img_meta.get("content"):
        main_image = absolutize(url, img_meta["content"])

    gallery = parse_gallery_images(soup, url)
    if not main_image and gallery:
        main_image = gallery[0]

    # Покупали N раз
    buyer_count = None
    buyer_el = soup.select_one(".buyer-count")
    if buyer_el:
        buyer_count = text_to_int(buyer_el.get_text())

    # Отзывы
    reviews_count = None
    rv1 = soup.select_one("#reviews-tab .reviews-count")
    if rv1:
        reviews_count = text_to_int(rv1.get_text())
    if reviews_count is None:
        m = re.search(r"Отзывы\s*\((\d+)\)", soup.get_text(" ", strip=True), re.I)
        if m:
            reviews_count = text_to_int(m.group(1))
    if reviews_count is None:
        el = soup.select_one(".reviews-count__mini, a.scroll_to_reviews")
        if el:
            reviews_count = text_to_int(el.get_text())

    # Описания
    desc_html = None
    desc_node = soup.select_one('[itemprop="description"]')
    if desc_node:
        try:
            desc_html = desc_node.decode_contents()
        except Exception:
            desc_html = desc_node.get_text("\n", strip=True)

    desc_text_short = None
    if desc_node:
        desc_text_short = " ".join(desc_node.get_text(" ", strip=True).split())

    # Характеристики
    properties = parse_properties_table_strict(soup)

    # Варианты фасовки
    variants = parse_variants(soup)

    return {
        "id": prod_id,
        "sku": sku,
        "name": name,
        "url": url,
        "category": category,
        "base_price": base_price,
        "currency": currency,
        "price_valid_until": price_valid_until,
        "availability": availability,
        "main_image": main_image,
        "gallery": gallery,
        "buyer_count": buyer_count,
        "reviews_count": reviews_count,
        "description_html": desc_html,
        "description_text": desc_text_short,
        "properties": properties,
        "variants": variants,
    }


# ---------- СОХРАНЕНИЕ ----------

def save_products_csv(items: List[Dict], path: Path):
    fields = [
        "id", "sku", "name", "url", "category",
        "base_price", "currency", "price_valid_until", "availability",
        "main_image", "gallery_count", "buyer_count", "reviews_count",
        "description_text", "source_categories",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for it in items:
            row = it.copy()
            row["gallery_count"] = len(row.get("gallery") or [])
            dt = row.get("description_text") or ""
            if len(dt) > 300:
                dt = dt[:297] + "..."
            row["description_text"] = dt

            src = row.get("source_categories") or []
            row["source_categories"] = "; ".join(src)

            w.writerow({k: row.get(k) for k in fields})

def save_variants_csv(items: List[Dict], path: Path):
    fields = [
        "product_id", "product_url", "product_name",
        "weight_g", "price", "old_price",
        "data_discount_amount", "data_bonus", "option_name", "title",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for it in items:
            pid = it.get("id")
            purl = it.get("url")
            pname = it.get("name")
            for v in it.get("variants") or []:
                w.writerow({
                    "product_id": pid,
                    "product_url": purl,
                    "product_name": pname,
                    "weight_g": v.get("weight_g"),
                    "price": v.get("price"),
                    "old_price": v.get("old_price"),
                    "data_discount_amount": v.get("data_discount_amount"),
                    "data_bonus": v.get("data_bonus"),
                    "option_name": v.get("option_name"),
                    "title": v.get("title"),
                })


# ---------- ЗАГРУЗКА СПИСКА КАТЕГОРИЙ ----------

def load_categories_from_file_or_const() -> List[str]:
    """
    Если есть categories.txt — читаем из него (по одной ссылке на строку),
    иначе используем CATEGORIES из конфига.
    """
    file = Path("categories.txt")
    cats: List[str] = []
    if file.exists():
        for line in file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cats.append(ensure_trailing_slash(line))
    if not cats:
        cats = [ensure_trailing_slash(u) for u in CATEGORIES]
    return cats


# ---------- MAIN ----------

def main():
    # 0) Грузим список категорий
    category_urls = load_categories_from_file_or_const()
    print("Категорий к парсингу:", len(category_urls))
    for u in category_urls:
        print("  -", u)

    # 1) Сбор ссылок по всем категориям
    product_links: List[str] = []
    link_sources: Dict[str, List[str]] = {}  # url -> [source_category_urls]

    for cat in category_urls:
        try:
            links = iterate_category_pages(cat, MAX_PAGES)
            for lnk in links:
                product_links.append(lnk)
                link_sources.setdefault(lnk, [])
                if cat not in link_sources[lnk]:
                    link_sources[lnk].append(cat)
        except Exception as e:
            print(f"[!] Ошибка обхода категории {cat}: {e}")

    # удаляем дубликаты ссылок, сохраняя порядок
    seen = set()
    unique_links = []
    for lnk in product_links:
        if lnk not in seen:
            seen.add(lnk)
            unique_links.append(lnk)

    if not unique_links:
        print("Не найдено продуктовых ссылок по всем категориям.")
        return

    print(f"Всего уникальных ссылок товаров: {len(unique_links)}")

    # 2) Парсинг карточек
    items: List[Dict] = []
    for i, url in enumerate(unique_links, 1):
        try:
            print(f"[{i}/{len(unique_links)}] {url}")
            data = parse_product_page(url)
            data["source_categories"] = link_sources.get(url, [])
            print(f"  -> {data.get('name')!r} | base_price={data.get('base_price')} | variants={len(data.get('variants') or [])}")
            items.append(data)
        except Exception as e:
            print(f"  [!] Ошибка парсинга {url}: {e}")
        time.sleep(REQUEST_DELAY)

    # 3) Сохранение
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    save_products_csv(items, OUT_CSV_PRODUCTS)
    save_variants_csv(items, OUT_CSV_VARIANTS)

    print("\nГотово:")
    print(f"  JSON: {OUT_JSON.resolve()}  (товаров: {len(items)})")
    print(f"  CSV (products): {OUT_CSV_PRODUCTS.resolve()}")
    print(f"  CSV (variants): {OUT_CSV_VARIANTS.resolve()}")


if __name__ == "__main__":
    main()
