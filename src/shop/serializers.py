# serializers.py
from rest_framework import serializers
from .models import ProductExpensePurchase, ManufacturersExpense, SelectedProduct, ManufacturersIncome
from useraccount.models import Withdrawal

from moderation.models import AggregatedExpense


class SelectedProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    manufacturers = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SelectedProduct
        fields = ['id', 'status', 'quantity', 'amount', 'product', 'product_name', 'product_price', 'manufacturers']

    def get_manufacturers(self, obj):
        # Для ManyToMany поля нужно обрабатывать несколько производителей
        manufacturers = obj.product.manufacturers.all()
        return ", ".join([manufacturer.name for manufacturer in manufacturers])


class ProductExpensePurchaseSerializer(serializers.ModelSerializer):
    productexpenseposition_name = serializers.CharField(source='productexpenseposition.name', read_only=True)
    manufacturers_name = serializers.CharField(source='manufacturers.name', read_only=True)

    class Meta:
        model = ProductExpensePurchase
        fields = ['id', 'productexpenseposition', 'productexpenseposition_name',
                  'manufacturers', 'manufacturers_name', 'count', 'price', 'data', 'create']

class ManufacturersExpenseSerializer(serializers.ModelSerializer):
    manufacturers_name = serializers.CharField(source='manufacturers.name', read_only=True)
    manufacturersexpense_name = serializers.CharField(source='manufacturersexpense.name', read_only=True)

    class Meta:
        model = ManufacturersExpense
        fields = ['id', 'manufacturersexpense', 'manufacturers', 'manufacturers_name', 'manufacturersexpense_name', 'price', 'count', 'data', 'create']

class WithdrawalSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Withdrawal
        fields = ['id', 'user', 'amount', 'type_payment','manufacturers', 'create']

class ManufacturersIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturersIncome
        fields = ['id', 'price', 'create','manufacturers', 'data']



class AggregatedExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AggregatedExpense
        fields = ['store', 'data', 'revenue_by_products', 'expenses_by_products', 'expenses_by_store', 'expenses_by_employee', 'income']
