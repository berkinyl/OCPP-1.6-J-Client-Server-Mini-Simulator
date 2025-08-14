-- CreateTable
CREATE TABLE "BootNotification" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "chargePointVendor" TEXT NOT NULL,
    "chargePointModel" TEXT NOT NULL,
    "chargePointSerialNumber" TEXT,
    "chargeBoxSerialNumber" TEXT,
    "firmwareVersion" TEXT,
    "iccid" TEXT,
    "imsi" TEXT,
    "meterType" TEXT,
    "meterSerialNumber" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Heartbeat" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "StatusNotification" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "connectorId" INTEGER NOT NULL,
    "errorCode" TEXT NOT NULL,
    "info" TEXT,
    "status" TEXT NOT NULL,
    "timestamp" DATETIME,
    "vendorId" TEXT,
    "vendorErrorCode" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
