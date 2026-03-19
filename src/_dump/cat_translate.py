import json
import time
from googletrans import Translator

# Загрузка данных
with open("_info.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Настройка переводчика
translator = Translator()

# Языки для перевода
languages = ["en", "tr", "kk", "uz", "tg"]

# Обход объектов
for item in data:
    fields = item.get("fields", {})

    for field_name, field_value in list(fields.items()):
        # Ищем только поля с "_ru"
        if field_name.endswith("_ru") and field_value:
            base_name = field_name[:-3]  # убираем "_ru"

            for lang in languages:
                target_field = f"{base_name}_{lang}"

                # Пропускаем, если уже есть перевод
                if fields.get(target_field):
                    continue

                try:
                    translation = translator.translate(field_value, src="ru", dest=lang)
                    fields[target_field] = translation.text
                    print(f"✔️ {base_name}_ru -> {lang}: {translation.text}")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"❌ Ошибка при переводе '{field_value}' -> {lang}: {e}")

# Сохраняем результат
with open("_info_translated.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Перевод завершён и сохранён в _info_translated.json")
