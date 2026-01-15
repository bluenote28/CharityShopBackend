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
    img_url = models.URLField(null=True, blank=True)
    additional_images = models.JSONField(null=True)
    web_url = models.URLField(max_length=450)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    charity = models.ForeignKey(Charity, on_delete=models.CASCADE)
    category = models.CharField(max_length=100, null=True)
    category_list = models.JSONField(null=True)
    item_location = models.JSONField(null=True)
    condition = models.CharField(max_length=30, null=True)
    seller = models.JSONField(null=True)
    
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
