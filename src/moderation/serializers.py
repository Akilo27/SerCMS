# serializers.py
from rest_framework import serializers
from .models import Products, Manufacturers

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = '__all__'  # Включаем все поля модели Products
