import { PrismaClient } from "../generated/prisma/index.js";

const prisma = new PrismaClient();

export const createBootNotification = async (req, res) => {
  try {
    const data = req.body;


    if (!data.chargePointVendor || !data.chargePointModel) {
      return res.status(400).json({ error: "chargePointVendor and chargePointModel are required" });
    }

    const newLog = await prisma.bootNotification.create({
      data: {
        chargePointVendor: data.chargePointVendor,
        chargePointModel: data.chargePointModel,
        chargePointSerialNumber: data.chargePointSerialNumber,
        chargeBoxSerialNumber: data.chargeBoxSerialNumber,
        firmwareVersion: data.firmwareVersion,
        iccid: data.iccid,
        imsi: data.imsi,
        meterType: data.meterType,
        meterSerialNumber: data.meterSerialNumber,
        clientId: data.clientId,
      },
    });

    res.status(201).json(newLog);
  } catch (error) {
    console.error("Error creating BootNotification log:", error);
    res.status(500).json({ error: "Internal server error" + req.body });
  }
};

export const getAllBootNotifications = async (req, res) => {
  try {
    const logs = await prisma.bootNotification.findMany({
      orderBy: { createdAt: "desc" }, // newest first
    });
    res.json(logs);
  } catch (error) {
    console.error("Error fetching BootNotification logs:", error);
    res.status(500).json({ error: "Internal server error" });
  }
};

