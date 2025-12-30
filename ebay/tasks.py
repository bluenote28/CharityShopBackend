import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "charityshopbackend.settings")
django.setup()

def update_database(charity_id):

    try:
        from .load_data_to_db import DatabaseLoader

        loader = DatabaseLoader(charity_id)
        print("loader created")
        loader.load_items_to_db()
        print("loader finished")

    except Exception as e:
        print(f"Error updating database for charity {charity_id}: {e}")