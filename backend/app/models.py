
from django.db import models

class Merchant(models.Model):
    name = models.CharField(max_length=100)

class Ledger(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.IntegerField()
    type = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

class Payout(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.IntegerField()
    status = models.CharField(max_length=20)
    retries = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class Idempotency(models.Model):
    key = models.CharField(max_length=100, unique=True)
