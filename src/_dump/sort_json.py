import json

# Замените на путь к вашему JSON файлу
input_file = 'shop9991.json'
output_file = 'sorted_output_file.json'

# Открытие и чтение исходного JSON файла
with open(input_file, 'r', encoding='utf-8') as infile:
    data = json.load(infile)

# Сортировка данных по ключам, чтобы упорядочить по строкам
def sort_json(data):
    if isinstance(data, dict):
        return {k: sort_json(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        return [sort_json(item) for item in data]
    else:
        return data

# Применяем сортировку
sorted_data = sort_json(data)

# Запись отсортированных данных в новый JSON файл
with open(output_file, 'w', encoding='utf-8') as outfile:
    json.dump(sorted_data, outfile, indent=4, ensure_ascii=False)

print(f"JSON файл успешно отсортирован и сохранен в {output_file}")
