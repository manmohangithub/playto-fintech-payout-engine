import React, { useEffect, useState } from "react";

const API = "https://playto-fintech-payout-engine.onrender.com";
const MID = 1;

export default function App() {
  const [balance, setBalance] = useState(0);
  const [payouts, setPayouts] = useState([]);
  const [amount, setAmount] = useState("");

  const fetchData = async () => {
    try {
      const b = await fetch(`${API}/balance/${MID}/`).then(r => r.json());
      const p = await fetch(`${API}/payouts/${MID}/`).then(r => r.json());

      setBalance(b.balance || 0);
      setPayouts(p.data || []);
    } catch {
      console.log("backend sleeping...");
    }
  };

  const send = async () => {
    await fetch(`${API}/payout/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": Date.now().toString(),
      },
      body: JSON.stringify({
        merchant_id: MID,
        amount: Number(amount),
      }),
    });

    setAmount("");
    fetchData();
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div style={{ padding: 40 }}>
      <h1>Balance: ₹{(balance / 100).toFixed(2)}</h1>

      <input value={amount} onChange={e => setAmount(e.target.value)} />
      <button onClick={send}>Send</button>

      <h3>Payouts</h3>
      {payouts.map(p => (
        <p key={p.id}>{p.amount} - {p.status}</p>
      ))}
    </div>
  );
}