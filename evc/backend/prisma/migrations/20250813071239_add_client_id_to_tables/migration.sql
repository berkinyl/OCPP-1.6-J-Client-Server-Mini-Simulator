/*
  Warnings:

  - Added the required column `clientId` to the `BootNotification` table without a default value. This is not possible if the table is not empty.
  - Added the required column `clientId` to the `Heartbeat` table without a default value. This is not possible if the table is not empty.
  - Added the required column `clientId` to the `StatusNotification` table without a default value. This is not possible if the table is not empty.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_BootNotification" (
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
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "clientId" TEXT NOT NULL
);
INSERT INTO "new_BootNotification" ("chargeBoxSerialNumber", "chargePointModel", "chargePointSerialNumber", "chargePointVendor", "createdAt", "firmwareVersion", "iccid", "id", "imsi", "meterSerialNumber", "meterType") SELECT "chargeBoxSerialNumber", "chargePointModel", "chargePointSerialNumber", "chargePointVendor", "createdAt", "firmwareVersion", "iccid", "id", "imsi", "meterSerialNumber", "meterType" FROM "BootNotification";
DROP TABLE "BootNotification";
ALTER TABLE "new_BootNotification" RENAME TO "BootNotification";
CREATE TABLE "new_Heartbeat" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "clientId" TEXT NOT NULL
);
INSERT INTO "new_Heartbeat" ("createdAt", "id") SELECT "createdAt", "id" FROM "Heartbeat";
DROP TABLE "Heartbeat";
ALTER TABLE "new_Heartbeat" RENAME TO "Heartbeat";
CREATE TABLE "new_StatusNotification" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "connectorId" INTEGER NOT NULL,
    "errorCode" TEXT NOT NULL,
    "info" TEXT,
    "status" TEXT NOT NULL,
    "timestamp" DATETIME,
    "vendorId" TEXT,
    "vendorErrorCode" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "clientId" TEXT NOT NULL
);
INSERT INTO "new_StatusNotification" ("connectorId", "createdAt", "errorCode", "id", "info", "status", "timestamp", "vendorErrorCode", "vendorId") SELECT "connectorId", "createdAt", "errorCode", "id", "info", "status", "timestamp", "vendorErrorCode", "vendorId" FROM "StatusNotification";
DROP TABLE "StatusNotification";
ALTER TABLE "new_StatusNotification" RENAME TO "StatusNotification";
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
