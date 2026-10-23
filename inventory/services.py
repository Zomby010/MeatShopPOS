"""The only place stock levels change.

Every function here runs inside a transaction, locks the BranchStock row,
writes a StockMovement and updates the cached quantity together.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from .models import BranchStock, MovementType, StockMovement

QTY_STEP = Decimal("0.001")
MONEY_STEP = Decimal("0.01")


class StockError(Exception):
    pass


class InsufficientStock(StockError):
    pass


def q_qty(value):
    return Decimal(value).quantize(QTY_STEP, rounding=ROUND_HALF_UP)


def q_money(value):
    return Decimal(value).quantize(MONEY_STEP, rounding=ROUND_HALF_UP)


def get_stock(product, branch):
    row = BranchStock.objects.filter(product=product, branch=branch).first()
    return row.quantity if row else Decimal("0.000")


def _lock_stock(product, branch):
    BranchStock.objects.get_or_create(product=product, branch=branch)
    return BranchStock.objects.select_for_update().get(product=product, branch=branch)


def _check_quantity(product, quantity):
    if not product.unit.allows_decimal and quantity != quantity.to_integral_value():
        raise StockError(f"{product} is counted in whole {product.unit.code}; got {quantity}.")


@transaction.atomic
def post_movement(
    *,
    product,
    branch,
    movement_type,
    quantity_change,
    user=None,
    unit_cost=None,
    reference=None,
    reason="",
    allow_negative=False,
):
    """Add (or remove, if negative) stock and record why."""
    if movement_type not in MovementType.values:
        raise StockError(f"Unknown movement type {movement_type!r}.")
    change = q_qty(quantity_change)
    if change == 0:
        raise StockError("Quantity change cannot be zero.")
    _check_quantity(product, change)

    stock = _lock_stock(product, branch)
    before = stock.quantity
    after = before + change
    if after < 0 and not allow_negative:
        raise InsufficientStock(
            f"Only {before} {product.unit.code} of {product} at {branch}; cannot remove {-change}."
        )
    cost = q_money(product.average_cost if unit_cost is None else unit_cost)
    movement = StockMovement(
        product=product,
        branch=branch,
        movement_type=movement_type,
        quantity_change=change,
        quantity_before=before,
        quantity_after=after,
        unit_cost=cost,
        value_change=q_money(change * cost),
        reason=reason[:255],
        created_by=user if user and user.is_authenticated else None,
    )
    if reference is not None:
        movement.reference_type = ContentType.objects.get_for_model(reference)
        movement.reference_id = str(reference.pk)
    movement.save()
    stock.quantity = after
    stock.save(update_fields=["quantity", "updated_at"])
    return movement


@transaction.atomic
def set_opening_stock(*, product, branch, quantity, user=None, unit_cost=None, reason="Opening stock"):
    """Record opening stock. Only allowed before the product has any movement
    at the branch; after that, changes go through recounts."""
    if StockMovement.objects.filter(product=product, branch=branch).exists():
        raise StockError(
            f"{product} already has stock history at {branch}. Use a stock recount instead."
        )
    return post_movement(
        product=product,
        branch=branch,
        movement_type=MovementType.OPENING,
        quantity_change=quantity,
        user=user,
        unit_cost=unit_cost,
        reason=reason,
    )


def ledger_totals():
    """Sum of quantity_change per (product_id, branch_id) from the ledger."""
    from django.db.models import Sum

    rows = StockMovement.objects.values("product_id", "branch_id").annotate(total=Sum("quantity_change"))
    return {(r["product_id"], r["branch_id"]): r["total"] or Decimal(0) for r in rows}


def find_stock_mismatches():
    """Compare cached BranchStock with the ledger. Returns a list of
    (product_id, branch_id, cached, ledger) for every difference."""
    totals = ledger_totals()
    cached = {(s.product_id, s.branch_id): s.quantity for s in BranchStock.objects.all()}
    mismatches = []
    for key in set(totals) | set(cached):
        ledger = q_qty(totals.get(key, 0))
        have = q_qty(cached.get(key, 0))
        if ledger != have:
            mismatches.append((key[0], key[1], have, ledger))
    return mismatches


@transaction.atomic
def rebuild_stock():
    """Overwrite cached BranchStock from the ledger. Returns mismatches fixed."""
    mismatches = find_stock_mismatches()
    for product_id, branch_id, _cached, ledger in mismatches:
        BranchStock.objects.update_or_create(
            product_id=product_id, branch_id=branch_id, defaults={"quantity": ledger}
        )
    return mismatches
