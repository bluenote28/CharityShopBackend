from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ebay', '0010_remove_item_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='category',
            field=models.CharField(max_length=100, null=True),
        ),
    ]