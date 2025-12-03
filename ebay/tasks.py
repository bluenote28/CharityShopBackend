from ebay.load_data_to_db import DatabaseLoader

def update_database_job(charity_id):
    loader = DatabaseLoader(charity_id)
    loader.load_items_to_db()