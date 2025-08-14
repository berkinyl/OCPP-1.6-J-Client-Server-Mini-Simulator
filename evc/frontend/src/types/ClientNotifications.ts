import type { Heartbeat } from "./Heartbeat.js";
import type { BootNotification } from "./BootNotification.js";
import type { StatusNotification } from "./StatusNotification.js";
export interface ClientNotification {
    clientId: string;
    heartbeats: Heartbeat[];
    bootNotifications: BootNotification[];
    statusNotifications: StatusNotification[];
}