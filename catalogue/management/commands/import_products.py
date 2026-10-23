from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalogue.importer import import_products
from core.models import Branch


class Command(BaseCommand):
    help = "Import products from a CSV or Excel file (Bizkit template columns)."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--branch", required=True, help="Branch code that receives opening stock.")

    def handle(self, path, branch, **options):
        try:
            branch_obj = Branch.objects.get(code=branch)
        except Branch.DoesNotExist:
            raise CommandError(f"No branch with code {branch!r}.")
        file = Path(path)
        result = import_products(file.name, file.read_bytes(), branch=branch_obj)
        for line in result.warnings:
            self.stdout.write(self.style.WARNING(line))
        for line in result.errors:
            self.stdout.write(self.style.ERROR(line))
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {result.created}, updated {result.updated}, "
                f"opening stock on {result.opening_stock}, errors {len(result.errors)}."
            )
        )
