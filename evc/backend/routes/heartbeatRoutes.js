import express from "express";
import { createHeartbeat, getHeartbeats } from "../controllers/heartbeatController.js";

const router = express.Router();

router.post("/", createHeartbeat);
router.get("/", getHeartbeats);

export default router;