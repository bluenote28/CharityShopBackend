import redis

conn = redis.Redis(
    host='redis-14370.c244.us-east-1-2.ec2.cloud.redislabs.com',
    port=14370,
    decode_responses=True,
    username="default",
    password="*******",
)