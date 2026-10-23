import io
from decimal import Decimal

from django.core.management import call_command
from openpyxl import Workbook

from catalogue.importer import COLUMNS, import_products
from catalogue.models import PriceHistory, Product
from catalogue.services import save_product
from inventory.models import MovementType, StockMovement
from inventory.services import get_stock

D = Decimal


def test_new_product_average_cost_starts_at_buying_price(capon):
    assert capon.average_cost == D("400")


def test_average_cost_follows_buying_price_until_stock_exists(capon, branch):
    from inventory.services import set_opening_stock

    capon.buying_price = D("410")
    save_product(capon, None)
    assert capon.average_cost == D("410")
    set_opening_stock(product=capon, branch=branch, quantity=D("5"))
    capon.buying_price = D("450")
    save_product(capon, None)
    capon.refresh_from_db()
    assert capon.average_cost == D("410")


def test_price_changes_are_recorded(capon, manager, branch):
    from inventory.services import set_opening_stock

    set_opening_stock(product=capon, branch=branch, quantity=D("5"))
    capon.retail_price = D("650")
    capon.buying_price = D("420")
    save_product(capon, manager)
    changes = {h.field: h for h in PriceHistory.objects.filter(product=capon, old_value__isnull=False)}
    assert set(changes) == {"retail_price", "buying_price"}
    assert (changes["retail_price"].old_value, changes["retail_price"].new_value) == (D("600"), D("650"))
    assert changes["retail_price"].changed_by == manager
    capon.refresh_from_db()
    assert capon.average_cost == D("400")  # editing buying price does not rewrite cost of stock on hand


def _csv(rows):
    lines = [",".join(COLUMNS)] + [",".join(str(v) for v in r) for r in rows]
    return "\n".join(lines).encode()


def test_import_csv_creates_products_and_opening_stock(db, branch, manager):
    data = _csv([
        ["Beef Mince", "Beef", 620, 750, 700, 40, 5, "kg", "", "BEEF-MINCE"],
        ["Eggs Tray", "Eggs", 380, 450, 420, 20, 5, "trays", "6001", ""],
        ["Bad Unit", "Beef", 1, 2, 2, 1, 0, "bucket", "", ""],
    ])
    result = import_products("products.csv", data, branch=branch, user=manager)
    assert (result.created, result.updated, result.opening_stock) == (2, 0, 2)
    assert len(result.errors) == 1 and "bucket" in result.errors[0]
    mince = Product.objects.get(name="Beef Mince")
    assert mince.unit.code == "kg" and mince.is_weighed and mince.sku == "BEEF-MINCE"
    assert get_stock(mince, branch) == D(40)
    assert StockMovement.objects.get(product=mince).movement_type == MovementType.OPENING


def test_reimport_updates_prices_but_not_stock(db, branch):
    row = ["Beef Mince", "Beef", 620, 750, 700, 40, 5, "kg", "", ""]
    import_products("p.csv", _csv([row]), branch=branch)
    row[3], row[5] = 780, 99
    result = import_products("p.csv", _csv([row]), branch=branch)
    assert (result.created, result.updated, result.opening_stock) == (0, 1, 0)
    assert result.warnings
    mince = Product.objects.get(name="Beef Mince")
    assert mince.retail_price == D(780)
    assert get_stock(mince, branch) == D(40)


def test_import_xlsx_with_bizkit_header_spacing(db, branch):
    wb = Workbook()
    ws = wb.active
    ws.append([c if c != "Retail Price" else "Retail Price " for c in COLUMNS])
    ws.append(["Back Bacon 400gms", "Bacon", 650, 835.5, 800, 12, 3, "pieces", 6161100123456, "BB400"])
    out = io.BytesIO()
    wb.save(out)
    result = import_products("p.xlsx", out.getvalue(), branch=branch)
    assert result.errors == []
    bacon = Product.objects.get(name="Back Bacon 400gms")
    assert bacon.retail_price == D("835.50")
    assert bacon.barcode == "6161100123456"
    assert get_stock(bacon, branch) == D(12)


def test_seed_catalogue_is_idempotent(db):
    call_command("seed_catalogue")
    count = Product.objects.count()
    assert count > 50
    assert Product.objects.filter(name="Chicken Capon", unit__code="kg").exists()
    call_command("seed_catalogue")
    assert Product.objects.count() == count


def test_seed_demo_runs_and_ledger_matches(db):
    from inventory.services import find_stock_mismatches

    call_command("seed_demo")
    call_command("seed_demo")  # safe to run twice
    assert StockMovement.objects.count() > 0
    assert find_stock_mismatches() == []
