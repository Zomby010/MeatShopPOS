from decimal import Decimal

from django.core.management.base import BaseCommand

from catalogue.models import Category, Product, UnitOfMeasure
from catalogue.seed_data import FARMERS_CHOICE_PRODUCTS
from catalogue.services import save_product
from parties.models import Supplier


class Command(BaseCommand):
    help = "Load the starter Farmers Choice catalogue. Safe to run again: existing products are left alone."

    def handle(self, *args, **options):
        supplier, _ = Supplier.objects.get_or_create(
            name="Farmers Choice Ltd",
            defaults={"address": "Nairobi, Kenya", "phone": ""},
        )
        units = {u.code: u for u in UnitOfMeasure.objects.all()}
        created = 0
        for name, category_name, unit_code, price in FARMERS_CHOICE_PRODUCTS:
            if Product.objects.filter(name__iexact=name).exists():
                continue
            category, _ = Category.objects.get_or_create(name=category_name)
            unit = units[unit_code]
            save_product(
                Product(
                    name=name,
                    category=category,
                    unit=unit,
                    supplier=supplier,
                    retail_price=Decimal(str(price)),
                    is_weighed=unit.allows_decimal,
                ),
                user=None,
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Added {created} Farmers Choice products."))
