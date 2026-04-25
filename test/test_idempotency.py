import requests
import uuid

URL = "http://127.0.0.1:8000/payout/"

key = str(uuid.uuid4())

payload = {
    "merchant_id": 1,
    "amount": 3000
}

headers = {
    "Idempotency-Key": key
}

r1 = requests.post(URL, json=payload, headers=headers)
print("First:", r1.json())

r2 = requests.post(URL, json=payload, headers=headers)
print("Second:", r2.json())