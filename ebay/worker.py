import os
from urllib.parse import urlparse
import redis
from rq import Worker, Queue, Connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'charityshopbackend.settings')
import django

try:
    django.setup()
except RuntimeError:
    pass

print("Worker started...")

listen = ['high', 'default', 'low']

url = urlparse(os.environ.get("REDIS_URL"))
conn = redis.Redis(host=url.hostname, port=url.port, password=url.password, ssl=(url.scheme == "rediss"), ssl_cert_reqs=None)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()