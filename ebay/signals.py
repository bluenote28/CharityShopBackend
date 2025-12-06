from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from .models import Charity
from django.core.mail import send_mail
from django.conf import settings
from django.db import close_old_connections
import django_rq 
import redis
import os
from .tasks import update_database

def updateUser(sender, instance, **kwargs):
    user = instance
    if user.email != '':
        user.username = user.email


pre_save.connect(updateUser, sender=User)

def loadDatabase(sender, instance, **kwargs):
    
    print("Loading Database Signal Triggered")
    charity = instance
    charity_id = charity.id

    redis_url = os.getenv('REDIS_URL')
    
    redis_conn = redis.StrictRedis.from_url(redis_url, ssl_cert_reqs=None)

    queue = django_rq.get_queue('default', connection=redis_conn)

    queue.enqueue(update_database, charity_id, job_timeout=7200)
 
post_save.connect(loadDatabase, sender=Charity)


def registeredUser(sender, instance, created, **kwargs):
    
    if created:
        user = instance


        subject = "Welcome to The charity Shop"
        message = "We are glad you are here"

        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)

post_save.connect(registeredUser, sender=User)