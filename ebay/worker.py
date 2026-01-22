import os
import redis


REDIS_URL = os.getenv("HEROKU_REDIS_COPPER_URL", "redis://localhost:6379")

conn = redis.from_url(REDIS_URL, ssl_cert_reqs=None)