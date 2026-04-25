import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, models

from .models import Merchant, Ledger, Payout, Idempotency
from .tasks import process_payout


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
        print("BALANCE ERROR:", e)
        return JsonResponse({"error": "server_error"}, status=500)


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
        print("PAYOUT LIST ERROR:", e)
        return JsonResponse({"error": "server_error"}, status=500)


# ---------------- PAYOUT CREATE ----------------
@csrf_exempt
def payout(request):
    if request.method != "POST":
        return JsonResponse({"error": "invalid_method"}, status=405)

    try:
        data = json.loads(request.body)

        merchant_id = data.get("merchant_id")
        amount = data.get("amount")
        idem_key = request.headers.get("Idempotency-Key")

        # ---------- VALIDATION ----------
        if not merchant_id or not amount or not idem_key:
            return JsonResponse({"error": "missing_fields"}, status=400)

        amount = int(amount)

        # ---------- IDEMPOTENCY ----------
        if Idempotency.objects.filter(key=idem_key).exists():
            return JsonResponse({"status": "duplicate"})

        # ---------- TRANSACTION ----------
        with transaction.atomic():

            merchant = Merchant.objects.select_for_update().get(id=merchant_id)

            credits = Ledger.objects.filter(
                merchant=merchant, type="credit"
            ).aggregate(total=models.Sum("amount"))["total"] or 0

            debits = Ledger.objects.filter(
                merchant=merchant, type="debit"
            ).aggregate(total=models.Sum("amount"))["total"] or 0

            balance = credits - debits

            if balance < amount:
                return JsonResponse({"error": "insufficient_funds"}, status=400)

            payout = Payout.objects.create(
                merchant=merchant,
                amount=amount,
                status="pending",
                retries=0
            )

            Idempotency.objects.create(key=idem_key)

        # ---------- ASYNC (CELERY) ----------
        try:
            process_payout.delay(payout.id)

        except Exception as e:
            print("Celery failed → fallback to sync:", e)

            # ---------- FALLBACK (SYNC) ----------
            payout.status = "processing"
            payout.save()

            Ledger.objects.create(
                merchant=payout.merchant,
                amount=payout.amount,
                type="debit"
            )

            payout.status = "completed"
            payout.save()

        return JsonResponse({"status": "pending"})

    except Merchant.DoesNotExist:
        return JsonResponse({"error": "merchant_not_found"}, status=404)

    except Exception as e:
        print("PAYOUT ERROR:", e)
        return JsonResponse({"error": "server_error"}, status=500)