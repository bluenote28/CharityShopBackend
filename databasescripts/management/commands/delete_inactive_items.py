from django.core.management.base import BaseCommand
from databasescripts.delete_inactive_items import deleteInactiveItems


class Command(BaseCommand):
    help = "Delete eBay items that have been inactive for more than 14 days"

    def handle(self, *args, **options):
        deleteInactiveItems()
