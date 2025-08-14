import express from "express";
import { createBootNotification , getAllBootNotifications} from "../controllers/bootNotificationController.js";

const router = express.Router();

router.post("/", createBootNotification);
router.get("/", getAllBootNotifications);

export default router;