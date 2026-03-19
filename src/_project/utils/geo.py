import requests

# Простой маппинг стран к языкам
COUNTRY_LANGUAGE_MAP = {
    "RU": "ru",
    "US": "en",
    "GB": "en",
    "KZ": "ru",
    "UZ": "ru",
    "TR": "tr",
    "TJ": "ru",
    # дополни по необходимости
}

API_TOKEN = "2472030d6f522e"  # твой рабочий токен от ipinfo.io


def get_language_from_ip(ip):
    try:
        response = requests.get(f"https://api.ipinfo.io/lite/{ip}?token={API_TOKEN}")
        if response.status_code == 200:
            data = response.json()
            country_code = data.get("country_code")
            return COUNTRY_LANGUAGE_MAP.get(country_code, "en")
    except Exception as e:
        print(f"[GeoLang] Ошибка при определении языка по IP: {e}")
    return "en"  # fallback язык
