import React, { useEffect, useState } from "react";
import "./styles.css";

const API = "https://playto-fintech-payout-engine.onrender.com";
const MID = 1;

export default function App() {
  const [balance, setBalance] = useState(0);
  const [payouts, setPayouts] = useState([]);
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ---------------- FETCH DATA ----------------
  const fetchData = async () => {
    try {
      setError("");

      const bRes = await fetch(`${API}/balance/${MID}/`);
      const pRes = await fetch(`${API}/payouts/${MID}/`);

      if (!bRes.ok || !pRes.ok) {
        throw new Error("Backend error");
      }

      const bData = await bRes.json();
      const pData = await pRes.json();

      setBalance(bData.balance || 0);
      setPayouts(pData.data || []);

    } catch (err) {
      console.error(err);
      setError("Backend sleeping / first request delay...");
    }
  };

  // ---------------- SEND PAYOUT ----------------
  const send = async () => {
    try {
      if (!amount || isNaN(amount)) {
        alert("Enter valid amount");
        return;
      }

      setLoading(true);
      setError("");

      const res = await fetch(`${API}/payout/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": Date.now().toString(), // safer than crypto
        },
        body: JSON.stringify({
          merchant_id: MID,
          amount: Number(amount),
        }),
      });

      let data;
      try {
        data = await res.json();
      } catch {
        throw new Error("Invalid server response");
      }

      if (!res.ok) {
        throw new Error(data.error || "Payout failed");
      }

      setAmount("");
      fetchData();

    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to send payout");
    } finally {
      setLoading(false);
    }
  };

  // ---------------- AUTO REFRESH ----------------
  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // ---------------- UI ----------------
  return (
    <div className="app">

      {/* SIDEBAR */}
      <div className="sidebar">
        <h2>Playto</h2>
        <p className="sub">Fintech Dashboard</p>
      </div>

      {/* MAIN */}
      <div className="main">

        <div className="top">
          <h1>Dashboard</h1>
          <span className="live">● Live</span>
        </div>

        {/* ERROR */}
        {error && <div className="error">{error}</div>}

        {/* CARDS */}
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

        {/* PAYOUT FORM */}
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

        {/* TABLE */}
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
              {payouts.length === 0 ? (
                <tr>
                  <td colSpan="3">No payouts yet</td>
                </tr>
              ) : (
                payouts.map((p) => (
                  <tr key={p.id}>
                    <td>₹{(p.amount / 100).toFixed(2)}</td>
                    <td>
                      <span className={`badge ${p.status}`}>
                        {p.status}
                      </span>
                    </td>
                    <td>{p.retries}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

        </div>

      </div>
    </div>
  );
}