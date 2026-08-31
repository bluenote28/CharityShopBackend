from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import migrations, models


def add_search_vector(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            """
            ALTER TABLE ebay_item
            ADD COLUMN search_vector tsvector
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(category, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(seller_description, '')), 'C')
            ) STORED
            """
        )
        schema_editor.execute(
            "CREATE INDEX ebay_item_search_vector_gin ON ebay_item USING GIN (search_vector)"
        )
    else:
        schema_editor.execute(
            "ALTER TABLE ebay_item ADD COLUMN search_vector text NULL"
        )


def remove_search_vector(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP INDEX IF EXISTS ebay_item_search_vector_gin")
    schema_editor.execute("ALTER TABLE ebay_item DROP COLUMN IF EXISTS search_vector")


class Migration(migrations.Migration):

    dependencies = [
        ("ebay", "0026_item_donation_percentage_item_seller_description"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="item",
                    name="search_vector",
                    field=models.GeneratedField(
                        db_persist=True,
                        expression=(
                            SearchVector("name", config="english", weight="A")
                            + SearchVector("category", config="english", weight="B")
                            + SearchVector(
                                "seller_description", config="english", weight="C"
                            )
                        ),
                        output_field=SearchVectorField(),
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_search_vector, remove_search_vector),
            ],
        ),
    ]
