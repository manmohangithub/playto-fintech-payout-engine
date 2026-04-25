import React, { useEffect, useState } from "react";
import "./styles.css";

const API = "http://127.0.0.1:8000";
const MID = 1;

export default function App() {
  const [balance, setBalance] = useState(0);
  const [payouts, setPayouts] = useState([]);
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 🔹 Fetch data
  const fetchData = async () => {
    try {
      setError("");

      const b = await fetch(`${API}/balance/${MID}/`);
      const balanceData = await b.json();

      const p = await fetch(`${API}/payouts/${MID}/`);
      const payoutData = await p.json();

      setBalance(balanceData.balance);
      setPayouts(payoutData.data);

    } catch (err) {
      console.error("FETCH ERROR:", err);
      setError("Backend not reachable");
    }
  };

  // 🔹 Send payout
  const send = async () => {
    try {
      if (!amount) return;

      setLoading(true);
      setError("");

      const res = await fetch(`${API}/payout/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: JSON.stringify({
          merchant_id: MID,
          amount: parseInt(amount),
        }),
      });

      const data = await res.json();
      console.log("Response:", data);

      setAmount("");
      fetchData();

    } catch (err) {
      console.error("SEND ERROR:", err);
      setError("Failed to send payout");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const i = setInterval(fetchData, 3000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="app">
      <div className="sidebar">
        <h2>Playto</h2>
        <p className="sub">Fintech Dashboard</p>
      </div>

      <div className="main">
        <div className="top">
          <h1>Dashboard</h1>
          <span className="live">● Live</span>
        </div>

        {/* 🔥 Error Display */}
        {error && <div className="error">{error}</div>}

        <div className="cards">
          <div className="card">
            <p>Balance</p>
            <h2>₹{(balance / 100).toFixed(2)}</h2>
          </div>

          <div className="card">
            <p>Total Payouts</p>
            <h2>{payouts.length}</h2>
          </div>
        </div>

        <div className="card">
          <h3>Request Payout</h3>
          <div className="row">
            <input
              placeholder="Enter amount (paise)"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />

            <button onClick={send} disabled={loading}>
              {loading ? "Processing..." : "Send"}
            </button>
          </div>
        </div>

        <div className="card">
          <h3>Payout History</h3>

          <table>
            <thead>
              <tr>
                <th>Amount</th>
                <th>Status</th>
                <th>Retries</th>
              </tr>
            </thead>

            <tbody>
              {payouts.map((p) => (
                <tr key={p.id}>
                  <td>₹{(p.amount / 100).toFixed(2)}</td>
                  <td>
                    <span className={`badge ${p.status}`}>
                      {p.status}
                    </span>
                  </td>
                  <td>{p.retries}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}