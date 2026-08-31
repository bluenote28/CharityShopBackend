from django.contrib.postgres.indexes import GinIndex
from django.db import migrations


def add_category_list_gin(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        "CREATE INDEX ebay_item_category_list_gin "
        "ON ebay_item USING GIN (category_list jsonb_path_ops)"
    )


def drop_category_list_gin(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP INDEX IF EXISTS ebay_item_category_list_gin")


class Migration(migrations.Migration):

    dependencies = [
        ("ebay", "0027_item_search_vector"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddIndex(
                    model_name="item",
                    index=GinIndex(
                        fields=["category_list"],
                        name="ebay_item_category_list_gin",
                        opclasses=["jsonb_path_ops"],
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_category_list_gin, drop_category_list_gin),
            ],
        ),
    ]
