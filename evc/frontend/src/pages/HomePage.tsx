import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import BootNotificationPage from "./BootNotificationPage";
import HeartbeatPage from "./HeartbeatPage";
import StatusNotificationPage from "./StatusNotificationPage";
import ClientNotificationPage from "./ClientNotificationPage";

import "../styles/HomePage.css";
import HomeImage from "../assets/vestel--600.png"

export default function HomePage() {
  const navLinks = [
    { to: "/", label: "Home" },
    { to: "/boot-notifications", label: "Boot Notifications" },
    { to: "/heartbeat-notifications", label: "Heartbeat Notifications" },
    { to: "/status-notifications", label: "Status Notifications" },
    { to: "/client-notifications", label: "Client Notifications" },
  ];

  return (
    <Router>
      <header style={{ padding: "10px", marginBottom: 20 }}>
        <nav className="navbar">
          {navLinks.map(({ to, label }) => (
            <Link key={to} to={to} className="nav-link">
              {label}
            </Link>
          ))}
        </nav>
      </header>

      <main className="main-content">
        <Routes>
          <Route
            path="/"
            element={
              <div className="home-message" style={{ textAlign: "center" }}>
                <img
                  src={HomeImage}
                  alt="Home"
                  className="boing-image"
                  style={{ width: "150px", marginBottom: "15px", border: "4px solid #282c34", borderRadius: "12px" }}
                />
                <h1>Welcome to the Home Page!</h1>
              </div>
            }
          />
          <Route path="/boot-notifications" element={<BootNotificationPage />} />
          <Route path="/heartbeat-notifications" element={<HeartbeatPage />} />
          <Route path="/status-notifications" element={<StatusNotificationPage />} />
          <Route path="/client-notifications" element={<ClientNotificationPage />} />
          <Route path="*" element={<div>Page not found</div>} />
        </Routes>
      </main>
    </Router>
  );
}