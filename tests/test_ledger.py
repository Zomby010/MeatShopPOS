from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import transaction

from inventory.models import BranchStock, ImmutableMovementError, MovementType, StockMovement
from inventory.services import (
    InsufficientStock,
    StockError,
    find_stock_mismatches,
    get_stock,
    post_movement,
    set_opening_stock,
)

D = Decimal


def test_opening_stock_writes_movement_and_stock(capon, branch, manager):
    m = set_opening_stock(product=capon, branch=branch, quantity=D("50"), user=manager)
    assert m.movement_type == MovementType.OPENING
    assert (m.quantity_before, m.quantity_after, m.quantity_change) == (D(0), D(50), D(50))
    assert m.unit_cost == D("400.00")
    assert m.value_change == D("20000.00")
    assert m.created_by == manager
    assert get_stock(capon, branch) == D(50)


def test_opening_stock_only_once(capon, branch):
    set_opening_stock(product=capon, branch=branch, quantity=D("50"))
    with pytest.raises(StockError, match="recount"):
        set_opening_stock(product=capon, branch=branch, quantity=D("10"))


def test_stock_is_per_branch(capon, branch, other_branch):
    set_opening_stock(product=capon, branch=branch, quantity=D("50"))
    set_opening_stock(product=capon, branch=other_branch, quantity=D("8.5"))
    assert get_stock(capon, branch) == D(50)
    assert get_stock(capon, other_branch) == D("8.5")


def test_movement_chain_and_decimals(capon, branch):
    set_opening_stock(product=capon, branch=branch, quantity=D("10"))
    m = post_movement(product=capon, branch=branch, movement_type=MovementType.SALE, quantity_change=D("-2.375"))
    assert (m.quantity_before, m.quantity_after) == (D(10), D("7.625"))
    assert get_stock(capon, branch) == D("7.625")


def test_cannot_go_negative(capon, branch):
    set_opening_stock(product=capon, branch=branch, quantity=D("1"))
    with pytest.raises(InsufficientStock):
        post_movement(product=capon, branch=branch, movement_type=MovementType.SALE, quantity_change=D("-2"))
    assert get_stock(capon, branch) == D(1)
    assert StockMovement.objects.count() == 1


def test_whole_units_reject_fractions(make_product, piece, branch):
    eggs = make_product("Eggs", unit=piece, buying="12", retail="17")
    with pytest.raises(StockError, match="whole"):
        set_opening_stock(product=eggs, branch=branch, quantity=D("1.5"))


def test_zero_change_rejected(capon, branch):
    with pytest.raises(StockError):
        post_movement(product=capon, branch=branch, movement_type=MovementType.SALE, quantity_change=0)


def test_movements_cannot_be_edited_or_deleted(capon, branch):
    m = set_opening_stock(product=capon, branch=branch, quantity=D("5"))
    m.reason = "changed"
    with pytest.raises(ImmutableMovementError):
        m.save()
    with pytest.raises(ImmutableMovementError):
        m.delete()
    with pytest.raises(ImmutableMovementError), transaction.atomic():
        StockMovement.objects.all().delete()
    assert StockMovement.objects.count() == 1


def test_reference_is_stored(capon, branch, poultry):
    m = post_movement(
        product=capon, branch=branch, movement_type=MovementType.PURCHASE,
        quantity_change=D("3"), reference=poultry, unit_cost=D("390"),
    )
    m.refresh_from_db()
    assert m.reference == poultry
    assert m.unit_cost == D("390.00")


def test_rebuild_stock_detects_and_fixes_mismatch(capon, branch, capsys):
    set_opening_stock(product=capon, branch=branch, quantity=D("50"))
    post_movement(product=capon, branch=branch, movement_type=MovementType.SALE, quantity_change=D("-5"))
    assert find_stock_mismatches() == []
    BranchStock.objects.filter(product=capon).update(quantity=D("99"))  # simulate corruption
    assert find_stock_mismatches() == [(capon.pk, branch.pk, D("99.000"), D("45.000"))]

    call_command("rebuild_stock")
    assert "1 mismatch" in capsys.readouterr().out
    assert get_stock(capon, branch) == D(99)

    call_command("rebuild_stock", "--fix")
    assert get_stock(capon, branch) == D(45)
    assert find_stock_mismatches() == []
