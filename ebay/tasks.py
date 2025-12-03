from django_rq import job

@job
def update_database():
        from .models import Charity
        from .load_data_to_db import DatabaseLoader
        all_charities = Charity.objects.all()

        for charity in all_charities:
            loader = DatabaseLoader(charity.id)
            loader.load_items_to_db()