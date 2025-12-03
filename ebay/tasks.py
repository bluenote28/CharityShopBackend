from django_rq import job

@job
def update_database(charity_id):
        from .models import Charity
        from .load_data_to_db import DatabaseLoader

        loader = DatabaseLoader(charity_id)
        loader.load_items_to_db()