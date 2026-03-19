import csv
import json
import pandas as pd
import xml.etree.ElementTree as ET
from shop.models import ImportHistory, Manufacturers, Products, ProductsGallery
from django.core.exceptions import ValidationError
from django.utils import timezone


class FileImporter:
    def __init__(self, import_history: ImportHistory):
        self.import_history = import_history
        self.file = import_history.file
        self.file_type = import_history.file_type
        self.status = import_history.status

    def import_data(self):
        self.import_history.status = 'in_progress'
        self.import_history.started_at = timezone.now()
        self.import_history.save()

        try:
            if self.file_type == 'csv':
                self._import_csv()
            elif self.file_type == 'xls' or self.file_type == 'xlsx':
                self._import_excel()
            elif self.file_type == 'json':
                self._import_json()
            elif self.file_type == 'xml':
                self._import_xml()

            self.import_history.status = 'completed'
            self.import_history.finished_at = timezone.now()

        except Exception as e:
            self.import_history.status = 'failed'
            self.import_history.save()
            raise ValidationError(f"Ошибка при импорте данных: {str(e)}")

        self.import_history.save()

    def _import_csv(self):
        # Пример импорта CSV
        with open(self.file.path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                manufacturer = Manufacturers.objects.create(
                    name=row['name'],
                    email=row['email'],
                    phone=row['phone'],
                    # Добавьте другие поля по необходимости
                )
                # Добавление товаров
                Products.objects.create(
                    name=row['product_name'],
                    price=row['price'],
                    manufacturer=manufacturer,
                )

    def _import_excel(self):
        # Пример импорта Excel
        df = pd.read_excel(self.file.path)
        for index, row in df.iterrows():
            manufacturer = Manufacturers.objects.create(
                name=row['name'],
                email=row['email'],
                phone=row['phone'],
            )
            Products.objects.create(
                name=row['product_name'],
                price=row['price'],
                manufacturer=manufacturer,
            )

    def _import_json(self):
        # Пример импорта JSON
        with open(self.file.path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                manufacturer = Manufacturers.objects.create(
                    name=item['name'],
                    email=item['email'],
                    phone=item['phone'],
                )
                Products.objects.create(
                    name=item['product_name'],
                    price=item['price'],
                    manufacturer=manufacturer,
                )

    def _import_xml(self):
        # Пример импорта XML
        tree = ET.parse(self.file.path)
        root = tree.getroot()
        for elem in root.findall('manufacturer'):
            manufacturer = Manufacturers.objects.create(
                name=elem.find('name').text,
                email=elem.find('email').text,
                phone=elem.find('phone').text,
            )
            Products.objects.create(
                name=elem.find('product_name').text,
                price=elem.find('price').text,
                manufacturer=manufacturer,
            )
