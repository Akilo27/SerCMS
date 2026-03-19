from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Products, Categories, Atribute


class ProductsResource(resources.ModelResource):
    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ForeignKeyWidget(Categories, "name"),
    )
    atribute = fields.Field(
        column_name="atribute",
        attribute="atribute",
        widget=ForeignKeyWidget(
            Atribute, "name"
        ),  # Убедитесь, что нет лишних параметров!
    )

    class Meta:
        model = Products
        fields = ("id", "name", "price", "quantity", "review_rating")
