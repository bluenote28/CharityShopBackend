from django.db import models
from django.contrib.auth.models import User

class Charity(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    id = models.AutoField(primary_key=True)
    ebay_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    img_url = models.URLField()
    web_url = models.URLField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    charity = models.ForeignKey(Charity, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class FavoriteList(models.Model):
    id = models.AutoField(primary_key=True, )
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Item, blank=True)
    charities = models.ManyToManyField(Charity, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FavoriteList of User {self.user_id}"
