from rest_framework.views import APIView
from rest_framework.response import Response
import os
import django_rq 
import redis
from rest_framework.permissions import IsAdminUser
from ebay.tasks import update_database
from django.db import close_old_connections
from .database_actions import deleteCharity, addCharity
from rq import Queue
from ebay.worker import conn

class RefreshDatabaseView(APIView):

    def __init__(self):
        super().__init__()

    permission_classes = [IsAdminUser]
    
    def post(self, request):
      
        charity_id = request.data['id']

        close_old_connections()

        q = Queue(connection=conn)
        q.enqueue(update_database, charity_id, job_timeout=7200)

        return Response("success")