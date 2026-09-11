from django.core.cache import caches
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from rq import Queue

from databasescripts.refresh_database import refreshDatabase
from ebay.worker import get_redis

disk = caches['diskcache']


class Command(BaseCommand):
    help = "Enqueue a full database refresh (or run it in this process with --now)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--charity-id',
            type=int,
            default=None,
            help='Refresh a single charity instead of all stale charities.',
        )
        parser.add_argument(
            '--now',
            action='store_true',
            help='Run in this process instead of enqueueing to the RQ worker.',
        )

    def handle(self, *args, **options):
        close_old_connections()
        charity_id = options['charity_id']

        if options['now']:
            refreshDatabase(charity_id)
            self.stdout.write(self.style.SUCCESS('refreshDatabase finished'))
            return

        q = Queue(connection=get_redis())
        q.enqueue(refreshDatabase, charity_id, job_timeout=172000)
        disk.clear()
        self.stdout.write(self.style.SUCCESS('refreshDatabase enqueued'))
