import logging
from django.utils import translation
from ipware import get_client_ip
import requests

API_TOKEN = "2472030d6f522e"  # ваш токен от ipinfo.io
LOG_FILE_PATH = "geolang.log"

# Настройка логгера
logger = logging.getLogger("geolang")
logger.setLevel(logging.DEBUG)
if not logger.hasHandlers():
    fh = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def get_language_from_ip(ip):
    logger.debug(f"Полученный IP: {ip}")
    if not ip:
        logger.debug("IP отсутствует, возвращаем 'en'")
        return "en"

    try:
        response = requests.get(
            f"https://api.ipinfo.io/lite/{ip}?token={API_TOKEN}", timeout=2
        )
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Ответ API: {data}")
            country_code = data.get("country_code")
            logger.debug(f"country_code: {country_code}")
            if country_code == "RU":
                return "ru"
            return "en"
        else:
            logger.warning(f"Ошибка HTTP: статус {response.status_code}")
    except Exception as e:
        logger.error(f"Исключение при запросе API: {e}")

    return "en"


class CountryBasedLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.debug("Middleware вызван")

        language = request.COOKIES.get("django_language")
        if language:
            logger.debug(f"Язык из cookies: {language}")
        else:
            ip, is_routable = get_client_ip(request)
            logger.debug(f"IP пользователя: {ip} (routable: {is_routable})")

            # Для локальной разработки можно подменять IP, если надо
            if ip in ("127.0.0.1", "::1", None):
                test_ip = "83.220.239.169"  # пример IP из России
                logger.debug(f"Локальный IP обнаружен, подменяем на {test_ip}")
                ip = test_ip

            language = get_language_from_ip(ip)
            logger.debug(f"Определён язык по IP: {language}")

        translation.activate(language)
        request.LANGUAGE_CODE = language

        response = self.get_response(request)

        # Устанавливаем куку только если её нет (чтобы не перезаписывать при ручной смене)
        if not request.COOKIES.get("django_language"):
            logger.debug(f"Установка cookie django_language={language}")
            response.set_cookie("django_language", language)

        return response
