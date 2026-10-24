from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from catalogue.models import Product
from catalogue.services import save_product
from core.models import Branch, Role, StaffProfile
from inventory.models import StockMovement
from inventory.services import set_opening_stock
from parties.models import Customer

# Demo prices for cuts with no Farmers Choice reference price.
# (retail, wholesale, buying) in KES. Not real prices.
DEMO_PRICES = {
    "Chicken Capon": (600, 560, 400),
    "Whole Chicken": (550, 520, 420),
    "Chicken Breast": (800, 760, 520),
    "Chicken Thighs": (650, 620, 430),
    "Chicken Boneless": (900, 850, 600),
    "Chicken Back": (300, 280, 180),
    "Chicken Wings": (550, 520, 360),
    "Chicken Drumsticks": (650, 620, 430),
    "Beef Stew (Steak & Bone)": (650, 620, 500),
    "Beef Mince": (750, 700, 620),
    "Beef Boneless Topside": (850, 800, 680),
    "Beef T-Bone": (900, 850, 700),
    "Beef Liver": (600, 560, 450),
    "Pork Loin Chops": (900, 850, 680),
    "Pork Belly Ribs": (850, 800, 640),
    "Pork Leg": (750, 700, 560),
    "Eggs (Tray of 30)": (450, 420, 380),
    "Eggs (Single)": (17, 15, 12.7),
}

STAFF = [
    ("owner", "Olive", "Owner", Role.OWNER, None, "1111"),
    ("manager", "Mark", "Manager", Role.MANAGER, "MAIN", "2222"),
    ("cashier1", "Cate", "Cashier", Role.CASHIER, "MAIN", "3333"),
    ("cashier2", "Kevin", "Cashier", Role.CASHIER, "MARKET", "4444"),
]


class Command(BaseCommand):
    help = "Create demo branches, staff, catalogue, prices, customers and opening stock. For testing only."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="meatpos-demo", help="Password for all demo users.")

    @transaction.atomic
    def handle(self, *args, password, **options):
        main, _ = Branch.objects.get_or_create(
            code="MAIN", defaults={"name": "Main Shop (Town Centre)", "is_main": True}
        )
        market, _ = Branch.objects.get_or_create(code="MARKET", defaults={"name": "Market Branch"})
        branches = {"MAIN": main, "MARKET": market}

        User = get_user_model()
        for username, first, last, role, branch_code, pin in STAFF:
            user, created = User.objects.get_or_create(
                username=username, defaults={"first_name": first, "last_name": last}
            )
            if created:
                user.set_password(password)
                user.save()
            profile, _ = StaffProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.branch = branches.get(branch_code)
            profile.set_pin(pin)
            profile.save()
        owner = User.objects.get(username="owner")

        call_command("seed_catalogue", stdout=self.stdout)

        for product in Product.objects.all():
            if product.name in DEMO_PRICES:
                retail, wholesale, buying = (Decimal(str(v)) for v in DEMO_PRICES[product.name])
            elif product.retail_price:
                retail = product.retail_price
                wholesale = (retail * Decimal("0.93")).quantize(Decimal("0.01"))
                buying = (retail * Decimal("0.78")).quantize(Decimal("0.01"))
            else:
                continue
            if product.buying_price:
                continue  # already priced; leave it alone
            product.retail_price, product.wholesale_price, product.buying_price = retail, wholesale, buying
            product.max_discount_percent = Decimal(5)
            product.low_stock_level = Decimal(5)
            save_product(product, owner)

        stocked = 0
        for i, product in enumerate(Product.objects.filter(buying_price__gt=0).order_by("name")):
            for code, branch in branches.items():
                if StockMovement.objects.filter(product=product, branch=branch).exists():
                    continue
                qty = Decimal(20 + (i * 7) % 40) if code == "MAIN" else Decimal(5 + (i * 3) % 15)
                if product.name == "Chicken Capon" and code == "MAIN":
                    qty = Decimal(50)
                set_opening_stock(product=product, branch=branch, quantity=qty, user=owner)
                stocked += 1

        for name, kind, limit in [
            ("Walk-in customer", Customer.Type.RETAIL, 0),
            ("Mama Njeri Hotel", Customer.Type.WHOLESALE, 50000),
            ("Town Butchery Supplies", Customer.Type.WHOLESALE, 100000),
        ]:
            Customer.objects.get_or_create(
                name=name, defaults={"customer_type": kind, "credit_limit": limit, "branch": main}
            )

        self.stdout.write(self.style.SUCCESS(
            f"Demo ready: 2 branches, {len(STAFF)} staff (password '{password}', PINs 1111-4444), "
            f"{stocked} opening stock entries."
        ))
