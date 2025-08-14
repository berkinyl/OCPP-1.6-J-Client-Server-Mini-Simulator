import { useEffect, useState } from "react";
import api from "../utils/api.js";
import type { StatusNotification } from "../types/StatusNotification.js";

export default function StatusNotificationTable() {
  const [data, setData] = useState<StatusNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get("/status-notification")
      .then(res => {
        const responseData = Array.isArray(res.data) ? res.data : [res.data];
        setData(responseData);
      })
      .catch(err => setError(err.message || "Failed to fetch status notifications"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading status notifications...</p>;
  if (error) return <p>Error: {error}</p>;
  if (data.length === 0) return <p>No status notifications available.</p>;

  return (
    <table style={{ width: "100%", wordWrap:"break-word", tableLayout: "fixed" }} border={1} cellPadding={5}>
      <thead>
        <tr>
          <th>#</th>
          <th>Client ID</th>
          <th>Connector ID</th>
          <th>Error Code</th>
          <th>Info</th>
          <th>Status</th>
          <th>Timestamp</th>
          <th>Vendor ID</th>
          <th>Vendor Error Code</th>
          <th>Created At</th>
        </tr>
      </thead>
      <tbody>
        {data.map(
          (
            {
              clientId,
              connectorId,
              errorCode,
              info,
              status,
              timestamp,
              vendorId,
              vendorErrorCode,
              createdAt,
            },
            idx
          ) => (
            <tr key={idx}>
              <td>{idx + 1}</td>
              <td>{clientId}</td>
              <td>{connectorId}</td>
              <td>{errorCode}</td>
              <td>{info || "-"}</td>
              <td>{status}</td>
              <td>{timestamp ? new Date(timestamp).toLocaleString() : "-"}</td>
              <td>{vendorId || "-"}</td>
              <td>{vendorErrorCode || "-"}</td>
              <td>{new Date(createdAt).toLocaleString()}</td>
            </tr>
          )
        )}
      </tbody>
    </table>
  );
}