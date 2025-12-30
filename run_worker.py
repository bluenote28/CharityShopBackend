import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from redis import Redis
from rq import Worker, Queue

if __name__ == '__main__':
    redis_conn = Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'), ssl_cert_reqs=None)
    worker = Worker(['default'], connection=redis_conn)
    worker.work()