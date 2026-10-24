from django.core.management.base import BaseCommand

from catalogue.models import Product
from core.models import Branch
from inventory.services import find_stock_mismatches, rebuild_stock


class Command(BaseCommand):
    help = "Check cached stock levels against the stock movement ledger, and optionally fix them."

    def add_arguments(self, parser):
        parser.add_argument("--fix", action="store_true", help="Overwrite cached stock from the ledger.")

    def handle(self, *args, fix=False, **options):
        mismatches = rebuild_stock() if fix else find_stock_mismatches()
        if not mismatches:
            self.stdout.write(self.style.SUCCESS("Stock matches the ledger."))
            return
        products = Product.objects.in_bulk([m[0] for m in mismatches])
        branches = Branch.objects.in_bulk([m[1] for m in mismatches])
        for product_id, branch_id, cached, ledger in mismatches:
            self.stdout.write(
                f"{products[product_id]} @ {branches[branch_id]}: cached {cached}, ledger {ledger}"
            )
        verb = "Fixed" if fix else "Found"
        style = self.style.WARNING if fix else self.style.ERROR
        self.stdout.write(style(f"{verb} {len(mismatches)} mismatch(es)."))
        if not fix:
            self.stdout.write("Run with --fix to rebuild cached stock from the ledger.")
