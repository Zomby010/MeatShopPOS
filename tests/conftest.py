from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from catalogue.models import Category, Product, UnitOfMeasure
from catalogue.services import save_product
from core.models import Branch, Role, StaffProfile


@pytest.fixture
def branch(db):
    return Branch.objects.create(code="MAIN", name="Main Shop", is_main=True)


@pytest.fixture
def other_branch(db):
    return Branch.objects.create(code="MARKET", name="Market Branch")


def make_staff(username, role, branch, pin=None):
    user = get_user_model().objects.create_user(username=username, password="pass-12345")
    profile = StaffProfile(user=user, role=role, branch=branch)
    if pin:
        profile.set_pin(pin)
    profile.save()
    return user


@pytest.fixture
def owner(db):
    return make_staff("owner", Role.OWNER, None)


@pytest.fixture
def manager(branch):
    return make_staff("manager", Role.MANAGER, branch)


@pytest.fixture
def cashier(branch):
    return make_staff("cashier", Role.CASHIER, branch, pin="1234")


@pytest.fixture
def kg(db):
    return UnitOfMeasure.objects.get(code="kg")


@pytest.fixture
def piece(db):
    return UnitOfMeasure.objects.get(code="piece")


@pytest.fixture
def poultry(db):
    return Category.objects.create(name="Poultry")


@pytest.fixture
def make_product(poultry, kg):
    def _make(name, unit=None, buying="400", retail="600", **kwargs):
        product = Product(
            name=name,
            category=poultry,
            unit=unit or kg,
            buying_price=Decimal(buying),
            retail_price=Decimal(retail),
            **kwargs,
        )
        return save_product(product, None)

    return _make


@pytest.fixture
def capon(make_product):
    return make_product("Chicken Capon")
