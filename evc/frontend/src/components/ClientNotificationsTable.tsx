import type { ClientNotification } from "../types/ClientNotifications.js";

const ClientNotificationsTable = (props: { data: ClientNotification }) => {
    const data = props.data;
    if (!data) {
        return <p>No data to display.</p>;
    }

  const { clientId, heartbeats, bootNotifications, statusNotifications } = data;

  return (
    <div style={{ padding: "20px" }}>
      <h2>Notifications for Client ID: <span style={{color:"green",paddingLeft:"5px"}}>{clientId}</span></h2>

      {/* Heartbeat Table */}
      <h3>Heartbeat Logs</h3>
      <table border={1} cellPadding="5" style={{ width: "100%", wordWrap:"break-word", tableLayout: "fixed", marginBottom: "30px" }}>
        <thead>
          <tr>
            <th>#</th>
            <th>ID</th>
            <th>Created At</th>
            <th>Client ID</th>
          </tr>
        </thead>
        <tbody>
          {heartbeats.length > 0 ? (
            heartbeats.map((hb,index) => (
              <tr key={index}>
                <td>{index+1}</td>
                <td>{hb.id}</td>
                <td>{new Date(hb.createdAt).toLocaleString()}</td>
                <td>{hb.clientId}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={4}>No Heartbeat logs found.</td>
            </tr>
          )}
        </tbody>
      </table>

      {/* Boot Notification Table */}
      <h3>Boot Notifications</h3>
      <table border={1} cellPadding="5" style={{ marginBottom: "30px", width: "100%" }}>
        <thead>
          <tr>
            <th>#</th>
            <th>Vendor</th>
            <th>Model</th>
            <th>Serial Number</th>
            <th>Firmware Version</th>
            <th>ICCID</th>
            <th>IMSI</th>
            <th>Meter Type</th>
            <th>Meter Serial Number</th>
            <th>Created At</th>
            <th>Client ID</th>
          </tr>
        </thead>
        <tbody>
          {bootNotifications.length > 0 ? (
            bootNotifications.map((bn,index) => (
              <tr key={index}>
                <td>{index+1}</td>
                <td>{bn.chargePointVendor}</td>
                <td>{bn.chargePointModel}</td>
                <td>{bn.chargePointSerialNumber || "-"}</td>
                <td>{bn.firmwareVersion || "-"}</td>
                <td>{bn.iccid || "-"}</td>
                <td>{bn.imsi || "-"}</td>
                <td>{bn.meterType || "-"}</td>
                <td>{bn.meterSerialNumber || "-"}</td>
                <td>{new Date(bn.createdAt).toLocaleString()}</td>
                <td>{bn.clientId}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={11}>No Boot notifications found.</td>
            </tr>
          )}
        </tbody>
      </table>

      {/* Status Notification Table */}
      <h3>Status Notifications</h3>
      <table border={1} cellPadding="5" style={{ marginBottom: "30px", width: "100%" }}>
        <thead>
          <tr>
            <th>#</th>
            <th>Connector ID</th>
            <th>Status</th>
            <th>Error Code</th>
            <th>Info</th>
            <th>Timestamp</th>
            <th>Vendor ID</th>
            <th>Vendor Error Code</th>
            <th>Created At</th>
            <th>Client ID</th>
          </tr>
        </thead>
        <tbody>
          {statusNotifications.length > 0 ? (
            statusNotifications.map((sn,index) => (
              <tr key={index}>
                <td>{index + 1}</td>
                <td>{sn.connectorId}</td>
                <td>{sn.status}</td>
                <td>{sn.errorCode}</td>
                <td>{sn.info || "-"}</td>
                <td>{sn.timestamp ? new Date(sn.timestamp).toLocaleString() : "-"}</td>
                <td>{sn.vendorId || "-"}</td>
                <td>{sn.vendorErrorCode || "-"}</td>
                <td>{new Date(sn.createdAt).toLocaleString()}</td>
                <td>{sn.clientId}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={10}>No Status notifications found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default ClientNotificationsTable;