from rest_framework.views import APIView
from rest_framework.response import Response
import os
import django_rq 
import redis
from rest_framework.permissions import IsAdminUser
from ebay.tasks import update_database
from django.db import close_old_connections
from .database_actions import deleteCharity, addCharity

class RefreshDatabaseView(APIView):

    def __init__(self):
        super().__init__()

    permission_classes = [IsAdminUser]
    
    def post(self, request):
      
        charity_id = request.data['id']

        close_old_connections()

        redis_url = os.getenv('REDIS_URL')
        
        redis_conn = redis.StrictRedis.from_url(redis_url, ssl_cert_reqs=None)

        queue = django_rq.get_queue('default', connection=redis_conn)

        queue.enqueue(update_database, charity_id, job_timeout=7200)

        return Response("success")