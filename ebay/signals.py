from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from .models import Charity
from ebay.load_data_to_db import DatabaseLoader
from django.core.mail import send_mail
from django.conf import settings
from rq import Queue
from .worker import conn
from .tasks import update_database_job

def updateUser(sender, instance, **kwargs):
    user = instance
    if user.email != '':
        user.username = user.email


pre_save.connect(updateUser, sender=User)

def loadDatabase(sender, instance, **kwargs):
    
    print("Loading Database Signal Triggered")
    charity = instance
    charity_id = charity.id

    q = Queue(connection=conn)
    q.enqueue(update_database_job, charity_id, job_timeout=7200)
 
post_save.connect(loadDatabase, sender=Charity)


def registeredUser(sender, instance, created, **kwargs):
    
    if created:
        user = instance


        subject = "Welcome to The charity Shop"
        message = "We are glad you are here"

        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)

post_save.connect(registeredUser, sender=User)