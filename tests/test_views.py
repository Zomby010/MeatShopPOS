from decimal import Decimal

import pytest
from django.urls import reverse

from catalogue.models import Product
from core.models import Role, StaffProfile
from inventory.services import get_stock, set_opening_stock


def test_login_required(client, db):
    assert client.get(reverse("catalogue:product_list")).status_code == 302


def test_pin_login(client, cashier):
    profile = cashier.staff
    resp = client.post(reverse("core:pin_login"), {"staff": profile.pk, "pin": "0000"})
    assert resp.status_code == 200 and "Wrong PIN" in resp.content.decode()
    resp = client.post(reverse("core:pin_login"), {"staff": profile.pk, "pin": "1234"})
    assert resp.status_code == 302
    assert client.get(reverse("core:dashboard")).status_code == 200


def test_pin_lockout_after_five_failures(client, cashier):
    from django.core.cache import cache

    cache.clear()
    profile = cashier.staff
    for _ in range(5):
        client.post(reverse("core:pin_login"), {"staff": profile.pk, "pin": "0000"})
    resp = client.post(reverse("core:pin_login"), {"staff": profile.pk, "pin": "1234"})
    assert "Too many wrong PINs" in resp.content.decode()


@pytest.mark.parametrize("name", [
    "core:staff_list", "core:staff_create", "catalogue:product_create",
    "catalogue:product_import", "catalogue:category_list", "parties:supplier_list",
])
def test_cashier_blocked_from_manager_pages(client, cashier, name):
    client.force_login(cashier)
    assert client.get(reverse(name)).status_code == 403


def test_manager_blocked_from_owner_pages(client, manager):
    client.force_login(manager)
    assert client.get(reverse("core:branch_list")).status_code == 403


def test_all_pages_render_for_owner(client, owner, branch, capon):
    set_opening_stock(product=capon, branch=branch, quantity=Decimal("5"))
    client.force_login(owner)
    urls = [
        reverse("core:dashboard"), reverse("core:branch_list"), reverse("core:branch_create"),
        reverse("core:staff_list"), reverse("core:staff_create"),
        reverse("catalogue:product_list"), reverse("catalogue:product_list") + "?q=capon&low=1",
        reverse("catalogue:product_create"), reverse("catalogue:product_detail", args=[capon.pk]),
        reverse("catalogue:product_update", args=[capon.pk]), reverse("catalogue:category_list"),
        reverse("catalogue:product_import"), reverse("catalogue:import_template"),
        reverse("inventory:movement_list"), reverse("inventory:product_history", args=[capon.pk]),
        reverse("inventory:opening_stock", args=[capon.pk]),
        reverse("parties:supplier_list"), reverse("parties:supplier_create"),
        reverse("parties:customer_list"), reverse("parties:customer_create"),
    ]
    for url in urls:
        assert client.get(url).status_code == 200, url
    resp = client.get(reverse("catalogue:product_list"), HTTP_HX_REQUEST="true")
    assert b"<html" not in resp.content and b"Chicken Capon" in resp.content


def test_create_product_with_opening_stock(client, manager, branch, poultry, kg):
    client.force_login(manager)
    resp = client.post(reverse("catalogue:product_create"), {
        "name": "Chicken Breast", "category": poultry.pk, "unit": kg.pk, "is_weighed": "on",
        "buying_price": "520", "retail_price": "800", "wholesale_price": "760",
        "wholesale_min_qty": "10", "max_discount_percent": "5", "low_stock_level": "3",
        "is_active": "on", "opening_stock": "12.5",
    })
    assert resp.status_code == 302
    breast = Product.objects.get(name="Chicken Breast")
    assert breast.average_cost == Decimal("520")
    assert get_stock(breast, branch) == Decimal("12.5")
    assert breast.price_history.count() == 4


def test_product_history_filters(client, manager, branch, capon):
    from inventory.models import MovementType
    from inventory.services import post_movement

    set_opening_stock(product=capon, branch=branch, quantity=Decimal("50"), user=manager)
    post_movement(product=capon, branch=branch, movement_type=MovementType.SALE,
                  quantity_change=Decimal("-2"), user=manager, reason="Sale #1")
    client.force_login(manager)
    url = reverse("inventory:product_history", args=[capon.pk])
    body = client.get(url).content.decode()
    assert "Opening stock" in body and "Sale #1" in body
    body = client.get(url, {"movement_type": "SALE"}).content.decode()
    assert "Sale #1" in body and "t-opening" not in body


def test_manager_creates_cashier_only_in_own_branch(client, manager, branch, other_branch):
    client.force_login(manager)
    form = {"username": "newbie", "role": Role.OWNER, "branch": other_branch.pk,
            "password": "long-password-1", "pin": "5678", "is_active": "on"}
    resp = client.post(reverse("core:staff_create"), form)
    assert resp.status_code == 200  # owner role and other branch are not allowed
    form.update(role=Role.CASHIER, branch=branch.pk)
    assert client.post(reverse("core:staff_create"), form).status_code == 302
    profile = StaffProfile.objects.get(user__username="newbie")
    assert profile.role == Role.CASHIER and profile.branch == branch and profile.check_pin("5678")
    assert profile.user.groups.filter(name="Cashier").exists()


def test_owner_switches_branch(client, owner, branch, other_branch):
    client.force_login(owner)
    client.post(reverse("core:switch_branch"), {"branch": other_branch.pk})
    assert client.get(reverse("core:dashboard")).context["current_branch"] == other_branch


def test_api_products_and_stock(client, cashier, manager, branch, capon):
    set_opening_stock(product=capon, branch=branch, quantity=Decimal("7"))
    client.force_login(cashier)
    data = client.get("/api/v1/products/?q=capon").json()
    assert data["count"] == 1 and "average_cost" not in data["results"][0]
    stock = client.get("/api/v1/stock/").json()["results"]
    assert stock[0]["quantity"] == "7.000"
    client.force_login(manager)
    assert "average_cost" in client.get("/api/v1/products/").json()["results"][0]


def test_api_requires_login(client, db):
    assert client.get("/api/v1/products/").status_code in (401, 403)
