from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from .models import Charity
from django.core.mail import send_mail
from django.conf import settings
from django.db import close_old_connections
from databasescripts.refresh_database import refreshDatabase
from rq import Queue
from .worker import get_redis

def updateUser(sender, instance, **kwargs):
    user = instance
    if user.email != '':
        user.username = user.email

pre_save.connect(updateUser, sender=User)

def registeredUser(sender, instance, created, **kwargs):
    
    if created:
        user = instance
        subject = "Welcome to The charity Shop"
        message = "We are glad you are here"

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}") 

post_save.connect(registeredUser, sender=User)