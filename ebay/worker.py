import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "charityshopbackend.settings")
django.setup()

from rq import Worker, Queue
import os
import redis

LISTEN_QUEUES = ["default"]

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

conn = redis.from_url(REDIS_URL, ssl_cert_reqs=None)

def start_worker():
    queues = [Queue(name, conn) for name in LISTEN_QUEUES]

    worker = Worker(
        queues=queues,
        connection=conn,
    )
    worker.work(with_scheduler=False, logging_level="INFO", burst=False)

if __name__ == "__main__":
    start_worker()