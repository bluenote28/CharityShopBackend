import django_rq 

@job
def update_database_job(charity_id):
    from ebay.load_data_to_db import DatabaseLoader
    loader = DatabaseLoader(charity_id)
    loader.load_items_to_db()