import { useEffect, useState } from "react";
import api from "../utils/api";
import type{ BootNotification } from "../types/BootNotification.ts";

export default function BootNotificationTable() {
  const [data, setData] = useState<BootNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<BootNotification[]>("/bootNotification")
      .then((res) => setData(res.data))
      .catch(err => setError(err.message || "Failed to fetch status notifications"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading status notifications...</p>;
  if (error) return <p>Error: {error}</p>;
  if (data.length === 0) return <p>No status notifications available.</p>;

  return (
    <div>
      <table
      style={{ width: "100%", wordWrap:"break-word", tableLayout: "fixed" }}
       border={1} cellPadding={5}>
        <thead>
          <tr>
            <th>#</th>
            <th>Client ID</th>
            <th>Charge Point Vendor</th>
            <th>Charge Point Model</th>
            <th>Charge Point Serial Number</th>
            <th>Charge Box Serial Number</th>
            <th>Firmware Version</th>
            <th>ICCID</th>
            <th>IMSI</th>
            <th>Meter Type</th>
            <th>Meter Serial Number</th>
            <th>Created At</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => (
            <tr key={index}>
              <td>{index + 1}</td>
              <td>{item.clientId || "-"}</td>
              <td>{item.chargePointVendor || "-"}</td>
              <td>{item.chargePointModel || "-"}</td>
              <td>{item.chargePointSerialNumber || "-"}</td>
              <td>{item.chargeBoxSerialNumber || "-"}</td>
              <td>{item.firmwareVersion || "-"}</td>
              <td>{item.iccid || "-"}</td>
              <td>{item.imsi || "-"}</td>
              <td>{item.meterType || "-"}</td>
              <td>{item.meterSerialNumber || "-"}</td>
              <td>{new Date(item.createdAt).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}