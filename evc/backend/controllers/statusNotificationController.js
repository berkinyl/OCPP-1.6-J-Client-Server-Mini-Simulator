import { PrismaClient } from "../generated/prisma/index.js";

const prisma = new PrismaClient();

// POST - Create new status notification
export const createStatusNotification = async (req, res) => {
  try {
    const data = req.body;

    if (!data.connectorId || !data.status) {
      return res.status(400).json({ error: "connectorId and status are required" });
    }

    const newStatusNotification = await prisma.statusNotification.create({
      data: {
        connectorId: data.connectorId,
        status: data.status,
        errorCode: data.errorCode,
        info: data.info,
        timestamp: data.timestamp ? new Date(data.timestamp) : undefined,
        vendorId: data.vendorId,
        vendorErrorCode: data.vendorErrorCode,
        clientId: data.clientId,
      },
    });

    res.status(201).json(newStatusNotification);
  } catch (error) {
    console.error("Error creating StatusNotification log:", error);
    res.status(500).json({ error: "Internal server error" });
  }
};

// GET - Fetch all status notifications
export const getStatusNotifications = async (req, res) => {
  try {
    const notifications = await prisma.statusNotification.findMany({
      orderBy: { timestamp: "desc" },
    });
    res.json(notifications);
  } catch (error) {
    console.error("Error fetching status notifications:", error);
    res.status(500).json({ error: "Internal server error" });
  }
};