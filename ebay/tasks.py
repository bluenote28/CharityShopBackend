from django_rq import job


charity = None

@job('default', timeout=7200)
def update_database(charity_id):

    global charity 
    charity = charity_id

    try:
        from .load_data_to_db import DatabaseLoader

        loader = DatabaseLoader(charity_id)
        print("loader created")
        loader.load_items_to_db()
        print("loader finished")

    except Exception as e:
        print(f"Error updating database for charity {charity_id}: {e}")

if charity is not None:
    update_database.delay(charity)