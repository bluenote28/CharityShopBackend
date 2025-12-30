import os
import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

conn = redis.from_url(REDIS_URL, ssl_cert_reqs=None)