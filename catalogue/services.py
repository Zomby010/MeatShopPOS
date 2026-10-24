from .models import PriceHistory, Product


def save_product(product, user):
    """Save a product and record a PriceHistory row for each price that changed.

    Until the product has any stock history, its average cost simply follows
    the buying price. After that, only stock movements (purchases,
    conversions) change it.
    """
    old = Product.objects.filter(pk=product.pk).first() if not product._state.adding else None
    if old is None or not old.movements.exists():
        product.average_cost = product.buying_price
    if user and user.is_authenticated and not product.created_by_id:
        product.created_by = user
    product.save()
    for field in Product.PRICE_FIELDS:
        old_value = getattr(old, field) if old else None
        new_value = getattr(product, field)
        if old_value != new_value:
            PriceHistory.objects.create(
                product=product,
                field=field,
                old_value=old_value,
                new_value=new_value,
                changed_by=user if user and user.is_authenticated else None,
            )
    return product
