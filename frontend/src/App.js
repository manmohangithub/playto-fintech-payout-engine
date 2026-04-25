import React, { useEffect, useState } from "react";
import "./styles.css";

const API = "https://playto-fintech-payout-engine.onrender.com";
const MID = 1;

export default function App() {
  const [balance, setBalance] = useState(0);
  const [payouts, setPayouts] = useState([]);
  const [amount, setAmount] = useState("");
  const [error, setError] = useState("");

  const fetchData = async () => {
    try {
      const b = await fetch(`${API}/balance/${MID}/`);
      const p = await fetch(`${API}/payouts/${MID}/`);

      const bData = await b.json();
      const pData = await p.json();

      setBalance(bData.balance || 0);
      setPayouts(pData.data || []);
    } catch {
      setError("Backend waking up...");
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
          merchant_id: MID,
          amount: Number(amount),
        }),
      });
      setAmount("");
      fetchData();
    } catch {
      setError("Failed to send");
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="app">
      <div className="sidebar">
        <h2>Playto</h2>
      </div>

      <div className="main">
        <h1>Dashboard</h1>

        {error && <div className="error">{error}</div>}

        <div className="card">
          <h2>Balance ₹{(balance/100).toFixed(2)}</h2>
        </div>

        <div className="card">
          <input value={amount} onChange={e=>setAmount(e.target.value)} placeholder="Amount"/>
          <button onClick={send}>Send</button>
        </div>

        <div className="card">
          <h3>Payouts</h3>
          {payouts.map(p=>(
            <div key={p.id}>{p.amount} - {p.status}</div>
          ))}
        </div>
      </div>
    </div>
  );
}