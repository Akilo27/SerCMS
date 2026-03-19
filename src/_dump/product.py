# pip install selenium webdriver_manager beautifulsoup4
# wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# sudo apt install ./google-chrome-stable_current_amd64.deb


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv

# Настройка браузера
options = Options()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)
wait = WebDriverWait(driver, 10)


def parse_product(url):
    try:
        driver.get(url)

        # Ждём заголовок, чтобы убедиться, что страница загружена
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Название не найдено"

        new_price_tag = soup.select_one("#indirimliFiyat .spanFiyat")
        new_price = (
            new_price_tag.get_text(strip=True)
            if new_price_tag
            else "Новая цена не найдена"
        )

        product_code_tag = soup.find("span", class_="productcode")
        product_code = (
            product_code_tag.get("content", "Биржевой код не найден")
            if product_code_tag
            else "Биржевой код не найден"
        )

        desc_tag = soup.find("div", class_="pro-description")
        description = (
            desc_tag.get_text(strip=True) if desc_tag else "Описание не найдено"
        )

        sizes = []
        size_containers = soup.select(
            "div.eksecenekLine.kutuluvaryasyon span.right_line"
        )
        for container in size_containers:
            size_boxes = container.find_all("span", class_="size_box")
            for box in size_boxes:
                size_text = box.get_text(strip=True)
                if size_text:
                    sizes.append(size_text)

        image_tags = soup.select("div.SmallImages img")
        images = [img["src"] for img in image_tags if img.get("src")]

        # Извлечение breadcrumb категории
        breadcrumb_items = soup.select("ul.breadcrumb li[itemprop='itemListElement']")
        categories = []
        for li in breadcrumb_items[:-1]:  # Последний элемент — это товар
            name_span = li.find("span", itemprop="name")
            if name_span:
                categories.append(name_span.get_text(strip=True))
        full_category_path = (
            " > ".join(categories) if categories else "Категория не найдена"
        )

        return {
            "url": url,
            "title": title,
            "price": new_price,
            "product_code": product_code,
            "description": description,
            "sizes": sizes,
            "images": images,
            "category": full_category_path,
        }

    except Exception as e:
        print(f"Ошибка при обработке {url}: {e}")
        return None


# 🔗 Список ссылок для парсинга
urls = [
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantolon-32",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantolon-33",
    "https://www.braccas.com.tr/beli-yarim-lastikli-slim-fit-chino-crop-pantalon-34",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantalon-35",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantalon-36",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantalon-40",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantalon-41",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantalon-42",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantalon-43",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-pantalon-lacivert",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-ekose-pantalon-46",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-ekose-pantalon-47",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-cizgili-crop-pantolon-48",
    "https://www.braccas.com.tr/yan-lastikli-slim-fit-chino-pantalon-gri",
    "https://www.braccas.com.tr/slim-fit-jogger-bel-pantolon-lacivert",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-crop-pantalon-55",
    "https://www.braccas.com.tr/pamuk-keten-comfort-fit-jogger-bel-pantolon-59",
    "https://www.braccas.com.tr/pamuk-keten-comfort-fit-jogger-bel-pantolon-60",
    "https://www.braccas.com.tr/slim-fit-jogger-bel-pantolon-siyah",
    "https://www.braccas.com.tr/slim-fit-jogger-bel-pantolon-ekru",
    "https://www.braccas.com.tr/slimt-fit-jogger-bel-pantolon-bej",
    "https://www.braccas.com.tr/slim-fit-jogger-bel-pantolon-haki",
    "https://www.braccas.com.tr/straight-fit-ekose-pantolon-66",
    "https://www.braccas.com.tr/yan-lastikli-rahat-chino-pantalon-77",
    "https://www.braccas.com.tr/yan-lastikli-rahat-chino-pantalon-78",
    "https://www.braccas.com.tr/slim-fit-jogger-bel-pantolon-ekose-bej",
    "https://www.braccas.com.tr/beli-lastikli-dokulu-chino-pantolon-80",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-slim-fit-chino-pantolon-gri-176",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-slim-fit-chino-pantolon-siyah-177",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-slim-fit-chino-pantolon-acik-gri-178",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-slim-fit-chino-pantolon-bej-179",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-slim-fit-chino-pantolon-lacivert-180",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-slim-fit-chino-pantolon-siyah-181",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-relaxed-fit-chino-pantolon-antrasit-182",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-relaxed-fit-chino-pantolon-lacivert-183",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-relaxed-fit-chino-pantolon-siyah-184",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-relaxed-fit-jogger-pantolon-lacivert-185",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-relaxed-fit-jogger-pantolon-gri-186",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-relaxed-fit-jogger-pantolon-siyah-187",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-siyah-189",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-ribanali-slim-fit-chino-pantolon-ekru",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-ribanali-slim-fit-chino-pantolon-lacivert-191",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-ribanali-slim-fit-chino-pantolon-lacivert-192",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-karisimli-relaxed-fit-ekru-194",
    "https://www.braccas.com.tr/erkek-yandan-cepli-pileli-klasik-bel-paca-fermuar-detayli-siyah-196",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-paca-lastik-detayli-relaxed-lacivert-197",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-regular-fit-chino-pantolon-gri-201",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-slim-fit-chino-sort-gri-204",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-slim-fit-chino-sort-siyah-205",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-ribanali-slim-fit-chino-sort-mavi-206",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-pantolon-haki-210",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-pantolon-vizon-214",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-dokulu-kumas-relaxed-fit-jogger-sort-siyah-220",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-slim-fit-chino-sort-lacivert-228",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-slim-fit-chino-sort-siyah-229",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-slim-fit-chino-sort-bej-231",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-sort-vizon-236",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-sort-haki-237",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-sort-antrasit-238",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-sort-beyaz-239",
    "https://www.braccas.com.tr/kadin-yandan-takma-cepli-beli-lastikli-jogger-sort-lime-240",
    "https://www.braccas.com.tr/kadin-yandan-takma-cepli-beli-lastikli-jogger-sort-haki-241",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-karisimli-relaxed-fit-chino-sort-ekru-242",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-karisimli-relaxed-fit-chino-sort-bej-243",
    "https://www.braccas.com.tr/erkek-yandan-cepli-normal-bel-slim-fit-chino-pantolon-gri-244",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-sort-tas-246",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-gorunumlu-relaxed-fit-chino-sort-ekru-247",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-relaxed-fit-chino-sort-beyaz-248",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-relaxed-fit-chino-sort-siyah-249",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-relaxed-fit-chino-sort-bej-250",
    "https://www.braccas.com.tr/erkek-yandan-cepli-klasik-bel-relaxed-fit-chino-sort-lacivert-251",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-dokulu-kumas-relaxed-fit-jogger-sort-ekru-252",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-ve-pileli-slim-fit-jogger-pantolon-lacivert-253",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-ve-pileli-slim-fit-jogger-pantolon-bej-255",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-duble-paca-kordonlu-slim-fit-jogger-pantolon-siyah-256",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-slim-fit-jogger-pantolon-siyah-257",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-gorunumlu-relaxed-fit-chino-sort-acik-yesil-258",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-ve-pileli-slim-fit-jogger-pantolon-antrasit-259",
    "https://www.braccas.com.tr/kadin-yandan-cepli-pamuklu-chino-yuksek-bel-slim-fit-pantolon-siyah-260",
    "https://www.braccas.com.tr/kadin-yandan-cepli-pamuklu-chino-yuksek-bel-slim-fit-pantolon-lacivert-261",
    "https://www.braccas.com.tr/kadin-yandan-cepli-pamuklu-chino-yuksek-bel-slim-fit-pantolon-haki-262",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-duble-paca-kordonlu-slim-fit-jogger-pantolon-beyaz-263",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-jogger-sort-petrol-264",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-jogger-sort-kum-265",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-jogger-sort-yosun-266",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-jogger-sort-leylak-267",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-sort-siyah-268",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-dokulu-relaxed-fit-jogger-sort-lacivert-269",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-gorunumlu-relaxed-fit-chino-sort-vizon-270",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-relaxed-fit-pantolon-siyah-271",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-relaxed-fit-pantolon-tas-272",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-lastikli-relaxed-fit-pantolon-haki-273",
    "https://www.braccas.com.tr/kadin-keten-gorunumlu-yandan-cepli-beli-lastikli-relaxed-fit-pantolon-tas-274",
    "https://www.braccas.com.tr/kadin-keten-gorunumlu-yandan-cepli-beli-lastikli-relaxed-fit-pantolon-haki-275",
    "https://www.braccas.com.tr/kadin-keten-karisimli-yandan-cepli-beli-lastikli-relaxed-fit-pantolon-naturel-276",
    "https://www.braccas.com.tr/kadin-beli-lastikli-jogger-sort-haki-277",
    "https://www.braccas.com.tr/kadin-beli-lastikli-jogger-sort-siyah-278",
    "https://www.braccas.com.tr/kadin-beli-lastikli-jogger-sort-tas-279",
    "https://www.braccas.com.tr/erkek-chino-arka-cep-fleto-klasik-pantolon-bej-282",
    "https://www.braccas.com.tr/erkek-chino-arka-cep-fleto-klasik-pantolon-siyah-283",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-keten-gorunumlu-pamuk-sort-ekru-284",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-keten-gorunumlu-pamuk-sort-gri-285",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-keten-gorunumlu-pamuk-sort-haki-286",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-keten-gorunumlu-pamuk-sort-bej-287",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-keten-gorunumlu-pamuk-sort-lacivert-288",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-keten-pamuk-karisimli-slim-fit-sort-ekru-289",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-keten-pamuk-karisimli-slim-fit-sort-bej-290",
    "https://www.braccas.com.tr/erkek-beli-lastikli-bagcikli-keten-karisimli-slim-fit-jogger-sort-siyah-291",
    "https://www.braccas.com.tr/erkek-beli-lastikli-bagcikli-keten-karisimli-slim-fit-jogger-sort-yesil-292",
    "https://www.braccas.com.tr/erkek-beli-lastikli-bagcikli-keten-karisimli-slim-fit-jogger-sort-mavi-293",
    "https://www.braccas.com.tr/erkek-beli-lastikli-bagcikli-pamuk-keten-karisimli-slim-fit-jogger-sort-vizon-294",
    "https://www.braccas.com.tr/erkek-beli-lastikli-bagcikli-pamuk-keten-karisimli-slim-fit-jogger-sort-haki-295",
    "https://www.braccas.com.tr/erkek-modal-karsimli-chino-slim-fit-sort-mercan-296",
    "https://www.braccas.com.tr/erkek-modal-karsimli-chino-slim-fit-sort-lacivert-297",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-lastikli-keten-gorunumlu-relaxed-fit-chino-sort-bej-298",
    "https://www.braccas.com.tr/erkek-chino-arka-cep-fleto-klasik-pantolon-antrasit-299",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-pilili-gofre-slim-fit-pantolon-siyah-300",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-arka-cep-fermuarli-slim-fit-pantolon-siyah-306",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-arka-cep-fermuarli-slim-fit-pantolon-antrasit-307",
    "https://www.braccas.com.tr/kadin-beli-yarim-lastikli-cift-pilili-duble-paca-pantolon-tas-308",
    "https://www.braccas.com.tr/kadin-beli-yarim-lastikli-cift-pilili-duble-paca-pantolon-tas-309",
    "https://www.braccas.com.tr/kadin-cift-pilili-arka-cep-fleto-chino-pantolon-tas-310",
    "https://www.braccas.com.tr/kadin-cift-pilili-arka-cep-fleto-chino-pantolon-haki-311",
    "https://www.braccas.com.tr/kadin-cift-pilili-arka-cep-fleto-keten-karisimli-chino-pantolon-naturel-312",
    "https://www.braccas.com.tr/kadin-keten-karisimli-beli-yarim-lastikli-cift-pilili-duble-paca-pantolon-naturel-313",
    "https://www.braccas.com.tr/beli-yarim-lastikli-chino-slim-fit-crop-pantolon-siyah-314",
    "https://www.braccas.com.tr/kadin-pileli-beli-lastikli-ve-kusakli-dugmeli-jogger-sort-tas-315",
    "https://www.braccas.com.tr/kadin-pileli-beli-lastikli-ve-kusakli-dugmeli-jogger-sort-mavi-316",
    "https://www.braccas.com.tr/kadin-yandan-cepli-fermuar-ve-agraf-kapamali-relaxed-fit-pantolon-siyah-317",
    "https://www.braccas.com.tr/kadin-yandan-cepli-fermuar-ve-agraf-kapamali-relaxed-fit-pantolon-lacivert-318",
    "https://www.braccas.com.tr/kadin-yandan-cepli-fermuar-ve-agraf-kapamali-relaxed-fit-pantolon-tas-319",
    "https://www.braccas.com.tr/kadin-yandan-cepli-fermuar-ve-agraf-kapamali-relaxed-fit-pantolon-kahverengi-320",
    "https://www.braccas.com.tr/kadin-yandan-cepli-arka-cep-fleto-beli-lastikli-ve-pilili-slim-fit-pantolon-lacivert-321",
    "https://www.braccas.com.tr/kadin-yandan-cepli-arka-cep-fleto-beli-lastikli-ve-pilili-slim-fit-pantolon-siyah-322",
    "https://www.braccas.com.tr/kadin-yandan-cepli-arka-cep-fleto-beli-lastikli-ve-pilili-slim-fit-pantolon-tas-323",
    "https://www.braccas.com.tr/kadin-yandan-cepli-arka-cep-fleto-beli-lastikli-ve-pilili-slim-fit-pantolon-kahverengi-324",
    "https://www.braccas.com.tr/kadin-yandan-cepli-fermuar-ve-agraf-kapamali-slim-fit-pantolon-lacivert-325",
    "https://www.braccas.com.tr/kadin-yandan-cepli-beli-ve-pacasi-lastikli-relaxed-fit-jogger-pantolon-lacivert-326",
    "https://www.braccas.com.tr/erkek-yandan-cepli-bel-bagcikli-slim-fit-chino-kahverengi-pantolon-327",
    "https://www.braccas.com.tr/erkek-yandan-cepli-bel-bagcikli-fermuarli-slim-fit-chino-bej-pantolon-340",
    "https://www.braccas.com.tr/erkek-yandan-cepli-bel-bagcikli-fermuarli-slim-fit-chino-siyah-pantolon-341",
    "https://www.braccas.com.tr/erkek-beli-lastikli-slim-fit-ekoseli-gri-pantolon-342",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-bagcikli-jogger-acik-mavi-sort-343",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-bagcikli-jogger-gri-sort-344",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-bagcikli-jogger-lacivert-sort-345",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-bagcikli-jogger-bej-keten-sort-346",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-slim-fit-chino-crop-pantolon-koyu-gri-347",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-yarim-lastikli-slim-fit-chino-bej-pantolon-350",
    "https://www.braccas.com.tr/erkek-yandan-cepli-beli-yarim-lastikli-slim-fit-chino-lacivert-pantolon-351",
    "https://www.braccas.com.tr/erkek-beli-bagcikli-yandan-cepli-slim-fit-jogger-bej-pantolon-352",
    "https://www.braccas.com.tr/erkek-beli-bagcikli-yandan-cepli-slim-fit-jogger-siyah-pantolon-353",
    "https://www.braccas.com.tr/erkek-beli-bagcikli-yandan-cepli-yesil-jogger-pantolon-354",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-fermuarli-vizon-chino-pantolon-355",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-fermuarli-bej-chino-pantolon-356",
    "https://www.braccas.com.tr/erkek-pileli-dokumlu-genis-paca-vizon-baggy-pantolon-358",
    "https://www.braccas.com.tr/erkek-pileli-dokumlu-genis-paca-haki-baggy-pantolon-366",
    "https://www.braccas.com.tr/erkek-yandan-cepli-slim-fit-lacivert-chino-pantolon-367",
    "https://www.braccas.com.tr/erkek-yandan-cepli-slim-fit-gri-chino-pantolon-368",
    "https://www.braccas.com.tr/erkek-yandan-cepli-slim-fit-bej-chino-pantolon-369",
    "https://www.braccas.com.tr/erkek-yandan-cepli-dokulu-rahat-kalip-bej-pantolon-370",
    "https://www.braccas.com.tr/erkek-yandan-cepli-dokulu-rahat-kalip-tas-pantolon-371",
    "https://www.braccas.com.tr/erkek-pileli-dokumlu-genis-paca-siyah-baggy-pantolon-378",
    "https://www.braccas.com.tr/kadin-beli-lastikli-lacivert-pantolon",
    "https://www.braccas.com.tr/erkek-beli-lastikli-tas-chino-pantolon",
    "https://www.braccas.com.tr/erkek-beli-lastikli-vizon-chino-pantolon",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-fermuarli-siyah-chino-pantolon",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-fermuarli-lacivert-chino-pantolon",
    "https://www.braccas.com.tr/erkek-beli-yarim-lastikli-fermuarli-antrasit-chino-pantolon",
    "https://www.braccas.com.tr/erkek-siyah-jogger-fit-sort",
    "https://www.braccas.com.tr/erkek-siyah-jogger-sort",
    "https://www.braccas.com.tr/erkek-bej-jogger-fit-sort",
    "https://www.braccas.com.tr/erkek-lacivert-jogger-fit-sort",
    "https://www.braccas.com.tr/erkek-beli-lastikli-antrasit-chino-pantolon",
    "https://www.braccas.com.tr/erkek-antrasit-chino-pantolon",
    "https://www.braccas.com.tr/erkek-haki-slim-fit-keten-karisimli-cizgili-pantolon",
    "https://www.braccas.com.tr/erkek-bej-slim-fit-keten-karisimli-cizgili-pantolon",
    "https://www.braccas.com.tr/erkek-regular-fit-orta-bel-duz-paca-bej-pantolon",
    "https://www.braccas.com.tr/erkek-regular-fit-orta-bel-duz-paca-lacivert-pantolon",
    "https://www.braccas.com.tr/erkek-lastikli-bel-kordonlu-duble-paca-beyaz-sort",
    "https://www.braccas.com.tr/erkek-beyaz-jogger-fit-sort",
    "https://www.braccas.com.tr/erkek-slim-fit-orta-bel-siyah-pantolon",
    "https://www.braccas.com.tr/erkek-beli-lastikli-rahat-kesim-siyah-sort",
    "https://www.braccas.com.tr/erkek-beli-lastikli-siyah-sort",
    "https://www.braccas.com.tr/erkek-beli-lastikli-rahat-kesim-tas-sort",
    "https://www.braccas.com.tr/erkek-beli-lastikli-rahat-kesim-lacivert-sort",
    "https://www.braccas.com.tr/erkek-likrali-dokulu-gri-pantolon",
    "https://www.braccas.com.tr/erkek-likrali-dokulu-bej-pantolon",
    "https://www.braccas.com.tr/erkek-slim-fit-beli-baglamali-dokulu-siyah-pantolon",
    "https://www.braccas.com.tr/erkek-slim-fit-beli-baglamali-dokulu-lacivert-pantolon",
]

# 📦 Парсинг
results = []
for url in urls:
    print(f"Парсинг: {url}")
    data = parse_product(url)
    if data:
        results.append(data)

driver.quit()

# 📤 Сохранение
csv_file = "/home/vagiz/Desktop/spares_products.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "url",
            "title",
            "price",
            "product_code",
            "description",
            "sizes",
            "images",
            "category",
        ],
    )
    writer.writeheader()
    for product in results:
        product["sizes"] = ", ".join(product["sizes"])
        product["images"] = ", ".join(product["images"])
        writer.writerow(product)

print(f"Информация сохранена в {csv_file}")
