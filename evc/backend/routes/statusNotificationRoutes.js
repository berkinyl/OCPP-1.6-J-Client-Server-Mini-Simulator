import express from "express";
import { createStatusNotification, getStatusNotifications } from "../controllers/statusNotificationController.js";

const router = express.Router();

router.post("/", createStatusNotification);
router.get("/", getStatusNotifications);

export default router;