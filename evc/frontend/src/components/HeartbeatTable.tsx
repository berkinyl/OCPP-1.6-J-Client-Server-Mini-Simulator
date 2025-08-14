import { useEffect, useState } from "react";
import api from "../utils/api.ts"; // Your axios instance or similar
import type{ Heartbeat } from "../types/Heartbeat.ts";

export default function HeartbeatTable() {
  const [data, setData] = useState<Heartbeat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get("/heartbeat")
      .then(res => {
        // Assuming backend sends array or single object
        const responseData = Array.isArray(res.data) ? res.data : [res.data];
        setData(responseData);
      })
      .catch(err => setError(err.message || "Failed to fetch heartbeat data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading heartbeat notifications...</p>;
  if (error) return <p>Error: {error}</p>;
  if (data.length === 0) return <p>No heartbeat notifications available.</p>;

  return (
    <table style={{ width: "100%", wordWrap:"break-word", tableLayout: "fixed" }} border={1} cellPadding={5}>
      <thead>
        <tr>
          <th>#</th>
          <th>Client ID</th>
          <th>ID</th>
          <th>Created At</th>
        </tr>
      </thead>
      <tbody>
        {data.map(({ id, createdAt, clientId }, idx) => (
          <tr key={id}>
            <td>{idx + 1}</td>
            <td>{clientId}</td>
            <td>{id}</td>
            <td>{new Date(createdAt).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}