from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from ebay.tasks import update_database
from .delete_inactive_items import deleteInactiveItems
from django.db import close_old_connections
from django.core.cache import caches
from rq import Queue
from ebay.worker import get_redis

disk = caches['diskcache']

class RefreshDatabaseView(APIView):

    def __init__(self):
        super().__init__()

    permission_classes = [IsAdminUser]

    def post(self, request):

        charity_id = request.data['id']

        close_old_connections()

        q = Queue(connection=get_redis())
        q.enqueue(update_database, charity_id, job_timeout=10000,  result_ttl=3600, failure_ttl=86400)

        disk.clear()
        return Response("success")

    permission_classes = [IsAdminUser]

    def get(self, request):

        close_old_connections()

        q = Queue(connection=get_redis())

        q.enqueue(deleteInactiveItems, job_timeout=7200)

        disk.clear()
        return Response("success")

