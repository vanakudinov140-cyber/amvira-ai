-- AlterTable
ALTER TABLE "bookings" ADD COLUMN     "yclients_external_id" TEXT,
ADD COLUMN     "yclients_sync_status" VARCHAR(32),
ADD COLUMN     "yclients_sync_error" TEXT;
