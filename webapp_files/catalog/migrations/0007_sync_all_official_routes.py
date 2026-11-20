from importlib import import_module

from django.db import migrations


def sync_official_routes(apps, schema_editor):
    migration_0006 = import_module("catalog.migrations.0006_import_official_routes")
    migration_0006.import_official_routes(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_import_official_routes"),
    ]

    operations = [
        migrations.RunPython(sync_official_routes, migrations.RunPython.noop),
    ]
