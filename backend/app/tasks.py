import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models, transaction

from .models import Merchant, Ledger, Payout, Idempotency
from .tasks import process_payout   # ✅ sync task (no celery)


# ---------------- BALANCE ----------------
def balance(request, merchant_id):
    try:
        merchant = Merchant.objects.get(id=merchant_id)

        credits = Ledger.objects.filter(
            merchant=merchant, type="credit"
        ).aggregate(total=models.Sum("amount"))["total"] or 0

        debits = Ledger.objects.filter(
            merchant=merchant, type="debit"
        ).aggregate(total=models.Sum("amount"))["total"] or 0

        return JsonResponse({
            "balance": credits - debits
        })

    except Merchant.DoesNotExist:
        return JsonResponse({"error": "merchant_not_found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ---------------- PAYOUT LIST ----------------
def payouts(request, merchant_id):
    try:
        merchant = Merchant.objects.get(id=merchant_id)

        data = list(
            Payout.objects.filter(merchant=merchant)
            .order_by("-id")
            .values("id", "amount", "status", "retries")
        )

        return JsonResponse({"data": data})

    except Merchant.DoesNotExist:
        return JsonResponse({"error": "merchant_not_found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ---------------- PAYOUT CREATE ----------------
@csrf_exempt
def payout(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "invalid_method"}, status=405)

        # ✅ Safe JSON parse
        try:
            data = json.loads(request.body or "{}")
        except:
            return JsonResponse({"error": "invalid_json"}, status=400)

        merchant_id = data.get("merchant_id")
        amount = data.get("amount")
        idem_key = request.headers.get("Idempotency-Key")

        # ✅ Validation
        if not merchant_id or amount is None or not idem_key:
            return JsonResponse({"error": "missing_fields"}, status=400)

        amount = int(amount)

        # ✅ Idempotency check
        if Idempotency.objects.filter(key=idem_key).exists():
            return JsonResponse({"status": "duplicate"})

        with transaction.atomic():
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)

            credits = Ledger.objects.filter(
                merchant=merchant, type="credit"
            ).aggregate(total=models.Sum("amount"))["total"] or 0

            debits = Ledger.objects.filter(
                merchant=merchant, type="debit"
            ).aggregate(total=models.Sum("amount"))["total"] or 0

            balance = credits - debits

            # ❌ insufficient funds
            if balance < amount:
                return JsonResponse({"error": "insufficient_funds"}, status=400)

            # ✅ Create payout as pending first
            payout = Payout.objects.create(
                merchant=merchant,
                amount=amount,
                status="pending",
                retries=0
            )

            # ✅ Deduct immediately
            Ledger.objects.create(
                merchant=merchant,
                amount=amount,
                type="debit"
            )

            # ✅ Save idempotency
            Idempotency.objects.create(key=idem_key)

        # 🚀 PROCESS (NO CELERY)
        process_payout(payout.id)

        return JsonResponse({"status": "pending"})

    except Merchant.DoesNotExist:
        return JsonResponse({"error": "merchant_not_found"}, status=404)

    except Exception as e:
        print("ERROR:", e)
        return JsonResponse({"error": str(e)}, status=500)