from django.db import models


# 🔹 Merchant
class Merchant(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# 🔹 Ledger (tracks credits & debits)
class Ledger(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    type = models.CharField(max_length=10)  # credit / debit
    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 FIX

    def __str__(self):
        return f"{self.type} - {self.amount}"


# 🔹 Payout (async processing)
class Payout(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    status = models.CharField(max_length=20)  # pending, processing, completed, failed
    retries = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 FIX

    def __str__(self):
        return f"{self.amount} - {self.status}"


# 🔹 Idempotency (prevents duplicate requests)
class Idempotency(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    key = models.CharField(max_length=255, unique=True)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)  # 🔥 FIX

    def __str__(self):
        return self.key