from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import SyncModel, TimeStampedModel

MONEY = {"max_digits": 12, "decimal_places": 2}
QTY = {"max_digits": 12, "decimal_places": 3}


class Category(SyncModel):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class UnitOfMeasure(TimeStampedModel):
    code = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=50)
    allows_decimal = models.BooleanField(
        default=False, help_text="Ticked for weighed units such as kg."
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.code


class Product(SyncModel):
    name = models.CharField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="products")
    barcode = models.CharField(max_length=64, unique=True, null=True, blank=True)
    sku = models.CharField("SKU", max_length=64, unique=True, null=True, blank=True)
    supplier = models.ForeignKey(
        "parties.Supplier", on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    buying_price = models.DecimalField(
        **MONEY, default=0, help_text="Latest price paid to the supplier, per unit."
    )
    average_cost = models.DecimalField(
        **MONEY, default=0, help_text="Weighted average cost of stock on hand, per unit."
    )
    retail_price = models.DecimalField(**MONEY, default=0)
    wholesale_price = models.DecimalField(**MONEY, default=0)
    wholesale_min_qty = models.DecimalField(
        **QTY, default=0, help_text="Quantity at which wholesale price applies. 0 = never automatic."
    )
    max_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    low_stock_level = models.DecimalField(**QTY, default=0)
    is_weighed = models.BooleanField(default=False, help_text="Sold by weight on the scale.")
    is_active = models.BooleanField(default=True)

    PRICE_FIELDS = ("buying_price", "retail_price", "wholesale_price", "max_discount_percent")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def retail_margin(self):
        if not self.retail_price:
            return None
        return (self.retail_price - self.average_cost) / self.retail_price * Decimal(100)


class PriceHistory(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_history")
    field = models.CharField(max_length=40)
    old_value = models.DecimalField(**MONEY, null=True)
    new_value = models.DecimalField(**MONEY)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "price history"

    def __str__(self):
        return f"{self.product} {self.field}: {self.old_value} -> {self.new_value}"
