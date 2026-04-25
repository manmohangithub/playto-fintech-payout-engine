
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction
from .models import Merchant, Ledger, Payout, Idempotency

def home(request):
    return JsonResponse({"status": "running"})

def balance(request, merchant_id):
    merchant = Merchant.objects.get(id=merchant_id)
    credits = Ledger.objects.filter(merchant=merchant, type="credit").aggregate(total=models.Sum("amount"))["total"] or 0
    debits = Ledger.objects.filter(merchant=merchant, type="debit").aggregate(total=models.Sum("amount"))["total"] or 0
    return JsonResponse({"balance": credits - debits})

def payouts(request, merchant_id):
    merchant = Merchant.objects.get(id=merchant_id)
    data = list(Payout.objects.filter(merchant=merchant).values("id","amount","status","retries"))
    return JsonResponse({"data": data})

@csrf_exempt
def payout(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)

    data = json.loads(request.body or "{}")
    merchant_id = data.get("merchant_id")
    amount = data.get("amount")
    key = request.headers.get("Idempotency-Key")

    if not merchant_id or amount is None or not key:
        return JsonResponse({"error": "missing_fields"}, status=400)

    if Idempotency.objects.filter(key=key).exists():
        return JsonResponse({"status": "duplicate"})

    with transaction.atomic():
        merchant = Merchant.objects.get(id=merchant_id)

        credits = Ledger.objects.filter(merchant=merchant, type="credit").aggregate(total=models.Sum("amount"))["total"] or 0
        debits = Ledger.objects.filter(merchant=merchant, type="debit").aggregate(total=models.Sum("amount"))["total"] or 0

        if credits - debits < amount:
            return JsonResponse({"error": "insufficient_funds"}, status=400)

        Payout.objects.create(merchant=merchant, amount=amount, status="completed", retries=0)
        Ledger.objects.create(merchant=merchant, amount=amount, type="debit")
        Idempotency.objects.create(key=key)

    return JsonResponse({"status": "completed"})
