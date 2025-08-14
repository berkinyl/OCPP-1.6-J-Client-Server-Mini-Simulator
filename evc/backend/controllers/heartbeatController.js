import { PrismaClient } from "../generated/prisma/index.js";

const prisma = new PrismaClient();

export const createHeartbeat = async (req, res) => {
  try {
    // Since HeartbeatRequest has no properties, just log the current time
    const newHeartbeat = await prisma.heartbeat.create({
      data: {
        clientId: req.body.clientId, // Assuming clientId is passed in the request body
        // timestamp will default to now()
      },
    });
    res.status(201).json(newHeartbeat);
  } catch (error) {
    console.error("Error creating Heartbeat log:", error);
    res.status(500).json({ error: "Internal server error" });
  }
};

export const getHeartbeats = async (req, res) => {
  try {
    const heartbeats = await prisma.heartbeat.findMany({
      orderBy: { createdAt: 'desc' },
    });
    res.json(heartbeats);
  } catch (error) {
    console.error("Error fetching heartbeats:", error);
    res.status(500).json({ error: "Internal server error" });
  }
};