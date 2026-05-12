-- Forward-only alignment with prisma/schema.prisma (SSOT).
-- Baseline: 20250514100000_salon_domain

-- -----------------------------------------------------------------------------
-- 1) ScenarioCode enum: add values required by SSOT (Prisma ScenarioCode)
-- -----------------------------------------------------------------------------
ALTER TYPE "ScenarioCode" ADD VALUE 'CONSULTATION';
ALTER TYPE "ScenarioCode" ADD VALUE 'UPSELL';
ALTER TYPE "ScenarioCode" ADD VALUE 'REACTIVATION';

-- -----------------------------------------------------------------------------
-- 2) Seed scenarios for new enum members (dialogs.scenario_id will be NOT NULL)
-- -----------------------------------------------------------------------------
INSERT INTO "scenarios" ("id", "code", "name", "is_active", "created_at", "updated_at")
SELECT gen_random_uuid(), x.code, x.name, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM (
  VALUES
    ('CONSULTATION'::"ScenarioCode", 'Consultation'),
    ('UPSELL'::"ScenarioCode", 'Upsell'),
    ('REACTIVATION'::"ScenarioCode", 'Reactivation')
) AS x("code", "name")
WHERE NOT EXISTS (
  SELECT 1 FROM "scenarios" s WHERE s."code" = x."code"
);

-- -----------------------------------------------------------------------------
-- 3) dialogs.scenario_id: NOT NULL + FK ON DELETE RESTRICT (match Prisma)
-- -----------------------------------------------------------------------------
UPDATE "dialogs" d
SET "scenario_id" = (
  SELECT s."id"
  FROM "scenarios" s
  WHERE s."code" = 'CONSULTATION'::"ScenarioCode"
  ORDER BY s."created_at" ASC
  LIMIT 1
)
WHERE d."scenario_id" IS NULL;

ALTER TABLE "dialogs" DROP CONSTRAINT "dialogs_scenario_id_fkey";

ALTER TABLE "dialogs" ALTER COLUMN "scenario_id" SET NOT NULL;

ALTER TABLE "dialogs"
  ADD CONSTRAINT "dialogs_scenario_id_fkey"
  FOREIGN KEY ("scenario_id") REFERENCES "scenarios"("id")
  ON DELETE RESTRICT
  ON UPDATE CASCADE;

-- -----------------------------------------------------------------------------
-- 4) messages: soft delete + updated_at (Prisma @updatedAt / deletedAt)
-- -----------------------------------------------------------------------------
ALTER TABLE "messages" ADD COLUMN "updated_at" TIMESTAMP(3);

UPDATE "messages" SET "updated_at" = "created_at" WHERE "updated_at" IS NULL;

ALTER TABLE "messages" ALTER COLUMN "updated_at" SET NOT NULL;

ALTER TABLE "messages" ADD COLUMN "deleted_at" TIMESTAMP(3);

-- -----------------------------------------------------------------------------
-- 5) clients — indexes from SSOT
-- -----------------------------------------------------------------------------
CREATE INDEX "clients_phone_idx" ON "clients" ("phone");

CREATE INDEX "clients_telegram_idx" ON "clients" ("telegram");

CREATE INDEX "clients_whatsapp_idx" ON "clients" ("whatsapp");

CREATE INDEX "clients_client_type_deleted_at_idx" ON "clients" ("client_type", "deleted_at");

CREATE INDEX "clients_created_at_idx" ON "clients" ("created_at");

-- -----------------------------------------------------------------------------
-- 6) scenarios — indexes from SSOT
-- -----------------------------------------------------------------------------
CREATE INDEX "scenarios_is_active_deleted_at_idx" ON "scenarios" ("is_active", "deleted_at");

CREATE INDEX "scenarios_code_deleted_at_idx" ON "scenarios" ("code", "deleted_at");

-- -----------------------------------------------------------------------------
-- 7) dialogs — indexes from SSOT (dialogs_client_id_idx already exists)
-- -----------------------------------------------------------------------------
CREATE INDEX "dialogs_scenario_id_idx" ON "dialogs" ("scenario_id");

CREATE INDEX "dialogs_client_id_deleted_at_idx" ON "dialogs" ("client_id", "deleted_at");

CREATE INDEX "dialogs_client_id_status_deleted_at_idx" ON "dialogs" ("client_id", "status", "deleted_at");

CREATE INDEX "dialogs_scenario_id_status_deleted_at_idx" ON "dialogs" ("scenario_id", "status", "deleted_at");

CREATE INDEX "dialogs_channel_status_idx" ON "dialogs" ("channel", "status");

CREATE INDEX "dialogs_current_stage_status_idx" ON "dialogs" ("current_stage", "status");

CREATE INDEX "dialogs_created_at_idx" ON "dialogs" ("created_at");

-- -----------------------------------------------------------------------------
-- 8) dialog_states — indexes from SSOT
-- -----------------------------------------------------------------------------
CREATE INDEX "dialog_states_dialog_id_idx" ON "dialog_states" ("dialog_id");

CREATE INDEX "dialog_states_stage_created_at_idx" ON "dialog_states" ("stage", "created_at");

-- -----------------------------------------------------------------------------
-- 9) messages — indexes from SSOT (messages_dialog_id_idx already exists)
-- -----------------------------------------------------------------------------
CREATE INDEX "messages_dialog_id_created_at_idx" ON "messages" ("dialog_id", "created_at");

CREATE INDEX "messages_dialog_id_deleted_at_idx" ON "messages" ("dialog_id", "deleted_at");

CREATE INDEX "messages_dialog_id_role_created_at_idx" ON "messages" ("dialog_id", "role", "created_at");

CREATE INDEX "messages_role_created_at_idx" ON "messages" ("role", "created_at");

-- -----------------------------------------------------------------------------
-- 10) bookings — indexes from SSOT (bookings_client_id_idx, bookings_datetime_idx exist)
-- -----------------------------------------------------------------------------
CREATE INDEX "bookings_client_id_deleted_at_idx" ON "bookings" ("client_id", "deleted_at");

CREATE INDEX "bookings_client_id_datetime_idx" ON "bookings" ("client_id", "datetime");

CREATE INDEX "bookings_status_datetime_idx" ON "bookings" ("status", "datetime");
