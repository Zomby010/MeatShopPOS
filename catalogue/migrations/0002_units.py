import uuid

from django.db import migrations

UNITS = [("kg", "Kilogram", True), ("piece", "Piece", False), ("packet", "Packet", False), ("tray", "Tray", False)]


def create_units(apps, schema_editor):
    Unit = apps.get_model("catalogue", "UnitOfMeasure")
    for code, name, allows_decimal in UNITS:
        Unit.objects.get_or_create(
            code=code, defaults={"id": uuid.uuid4(), "name": name, "allows_decimal": allows_decimal}
        )


class Migration(migrations.Migration):
    dependencies = [("catalogue", "0001_initial")]
    operations = [migrations.RunPython(create_units, migrations.RunPython.noop)]
