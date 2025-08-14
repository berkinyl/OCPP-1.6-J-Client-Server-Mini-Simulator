import StatusNotificationTable from "../components/StatusNotificationTable";

export default function StatusNotificationPage() {
  return (
    <div style={{width:"1200px",boxSizing:"border-box"}}>
      <h1>EV Charging Status Notifications</h1>
      <StatusNotificationTable />
    </div>
  );
}