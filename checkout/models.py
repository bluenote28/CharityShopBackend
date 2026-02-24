from django.db import models
from ebay.models import Item


class CheckoutSession(models.Model):
    id = models.AutoField(primary_key=True)
    ebay_session_id = models.CharField(max_length=255, unique=True, db_index=True)
    buyer_email = models.EmailField()
    shipping_address = models.JSONField()
    ebay_response = models.JSONField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')

    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')

    items = models.ManyToManyField(Item, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CheckoutSession {self.ebay_session_id} ({self.status})"


class PurchaseOrder(models.Model):
    id = models.AutoField(primary_key=True)
    ebay_order_id = models.CharField(max_length=255, unique=True, db_index=True)
    checkout_session = models.OneToOneField(
        CheckoutSession,
        on_delete=models.CASCADE,
        related_name='purchase_order'
    )
    ebay_response = models.JSONField(null=True, blank=True)

    order_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PurchaseOrder {self.ebay_order_id} ({self.status})"
