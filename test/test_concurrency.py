import threading
import requests

URL = "http://127.0.0.1:8000/payout/"

def send_request():
    response = requests.post(
        URL,
        json={
            "merchant_id": 1,
            "amount": 6000
        },
        headers={
            "Idempotency-Key": str(threading.get_ident())
        }
    )
    print(response.status_code, response.json())


threads = []

# simulate 2 parallel payout requests
for _ in range(2):
    t = threading.Thread(target=send_request)
    threads.append(t)
    t.start()

for t in threads:
    t.join()