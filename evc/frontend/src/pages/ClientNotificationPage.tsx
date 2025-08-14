import { useState } from "react";
import ClientNotificationsTable from "../components/ClientNotificationsTable";
import type { ClientNotification } from "../types/ClientNotifications";
import api from "../utils/api";
export default function App() {
  const [clientId, setClientId] = useState("");
  const [data, setData] = useState<ClientNotification>();

const fetchNotifications = async () => {
  try {
    const res = await api.get<ClientNotification>(
      `/client-notifications/${clientId}`
    );
    setData(res.data);
  } catch (error) {
    console.error("Error fetching notifications:", error);
  }
};
  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "80vh",
      background: "#f5f5f5"
    }}>
      <div style={{
        borderRadius: "12px",
        boxShadow: "10px 10px 16px rgba(0,0,0,0.08)",
        padding: "32px 40px",
        minWidth: "350px",
        maxWidth: "1200px",
        width: "100%",
        background: "#f5f5f5"
      }}>
        <h1 style={{
          marginBottom: "24px",
          fontSize: "2rem",
          color: "#222"
        }}>Client Notifications</h1>
        <div style={{ display: "flex", gap: "12px", marginBottom: "24px" }}>
          <input
            type="text"
            placeholder="Enter Client ID"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            style={{
              flex: 1,
              padding: "10px 14px",
              borderRadius: "6px",
              border: "1px solid #dcdde1",
              fontSize: "1rem"
            }}
          />
          <button
            onClick={fetchNotifications}
            style={{
              padding: "10px 18px",
              borderRadius: "6px",
              background: "#0097e6",
              color: "#fff",
              border: "none",
              fontWeight: "bold",
              cursor: "pointer",
              fontSize: "1rem",
              transition: "background 0.2s"
            }}
            onMouseOver={e => (e.currentTarget.style.background = '#4078c0')}
            onMouseOut={e => (e.currentTarget.style.background = '#0097e6')}
          >
            Get Notifications
          </button>
        </div>
        {data && <ClientNotificationsTable data={data} />}
      </div>
    </div>
  );
}