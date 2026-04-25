const API = "https://playto-fintech-payout-engine.onrender.com";

const fetchData = async () => {
  try {
    const bRes = await fetch(`${API}/balance/1/`);
    if (!bRes.ok) throw new Error("Backend not ready");

    const bData = await bRes.json();

    const pRes = await fetch(`${API}/payouts/1/`);
    const pData = await pRes.json();

    setBalance(bData.balance || 0);
    setPayouts(pData.data || []);

  } catch (err) {
    console.log("Backend waking up...");
  }
};

const send = async () => {
  try {
    await fetch(`${API}/payout/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": Date.now().toString(),
      },
      body: JSON.stringify({
        merchant_id: 1,
        amount: Number(amount),
      }),
    });

    fetchData();
    setAmount("");

  } catch {
    alert("Backend not reachable (wait 5 sec and retry)");
  }
};