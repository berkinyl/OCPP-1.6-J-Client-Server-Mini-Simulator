import { PrismaClient } from "../generated/prisma/index.js";

const prisma = new PrismaClient();

export const getClientNotificationsByClientId = async (req, res) => {
  try {
    const { clientId } = req.params;

    if (!clientId) {
      return res.status(400).json({ error: 'Client ID is required' });
    }

    // Fetch from all three tables
    const [heartbeats, bootNotifications, statusNotifications] = await Promise.all([
      prisma.heartbeat.findMany({
        where: { clientId },
        orderBy: { createdAt: 'desc' }
      }),
      prisma.bootNotification.findMany({
        where: { clientId },
        orderBy: { createdAt: 'desc' }
      }),
      prisma.statusNotification.findMany({
        where: { clientId },
        orderBy: { createdAt: 'desc' }
      })
    ]);

    return res.json({
      clientId,
      heartbeats,
      bootNotifications,
      statusNotifications
    });

  } catch (error) {
    console.error('Error fetching client notifications:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
};