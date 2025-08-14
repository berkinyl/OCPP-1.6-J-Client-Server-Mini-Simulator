
import express from "express";
import { PrismaClient } from "./generated/prisma/index.js";
import bootNotificationRoutes from "./routes/bootNotificationRoutes.js";
import  heartbeatRoutes from "./routes/heartbeatRoutes.js";
import statusNotificationRoutes from "./routes/statusNotificationRoutes.js";
import clientNotificationRoutes from "./routes/clientNotificationRoutes.js";

import cors from "cors";


const app = express();
const prisma = new PrismaClient();

app.use(express.json());
app.use(cors());
app.use("/bootnotification", bootNotificationRoutes);
app.use("/heartbeat", heartbeatRoutes);
app.use("/status-notification", statusNotificationRoutes);
app.use("/client-notifications", clientNotificationRoutes);

app.get("/", (req, res) => {
  res.send("Backend is working");
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log('Server listening on port ${PORT}');
});
