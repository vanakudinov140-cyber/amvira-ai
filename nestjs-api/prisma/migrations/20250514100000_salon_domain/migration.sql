DROP TABLE IF EXISTS "seed_markers";

CREATE SCHEMA IF NOT EXISTS "public";

CREATE TYPE "ClientType" AS ENUM ('NEW', 'RETURNING', 'VIP');

CREATE TYPE "DialogChannel" AS ENUM ('TELEGRAM', 'WHATSAPP', 'API', 'WEBHOOK');

CREATE TYPE "DialogStage" AS ENUM ('TRUST_BUILDING', 'DISCOVERY', 'PRESENTATION', 'OBJECTION_HANDLING', 'BOOKING', 'COMPLETED');

CREATE TYPE "DialogStatus" AS ENUM ('ACTIVE', 'PAUSED', 'CLOSED');

CREATE TYPE "MessageRole" AS ENUM ('USER', 'ASSISTANT', 'SYSTEM', 'TOOL');

CREATE TYPE "BookingStatus" AS ENUM ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'NO_SHOW');

CREATE TYPE "ScenarioCode" AS ENUM ('HAIR_COLORING', 'HAIRCUT', 'BROWS', 'MAKEUP', 'RETENTION_CAMPAIGN');

CREATE TABLE "clients" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "phone" TEXT,
    "telegram" TEXT,
    "whatsapp" TEXT,
    "client_type" "ClientType" NOT NULL,
    "notes" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "deleted_at" TIMESTAMP(3),

    CONSTRAINT "clients_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "scenarios" (
    "id" UUID NOT NULL,
    "code" "ScenarioCode" NOT NULL,
    "name" TEXT NOT NULL,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "deleted_at" TIMESTAMP(3),

    CONSTRAINT "scenarios_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "dialogs" (
    "id" UUID NOT NULL,
    "client_id" UUID NOT NULL,
    "current_stage" "DialogStage" NOT NULL,
    "status" "DialogStatus" NOT NULL,
    "channel" "DialogChannel" NOT NULL,
    "scenario_id" UUID,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "deleted_at" TIMESTAMP(3),

    CONSTRAINT "dialogs_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "dialog_states" (
    "id" UUID NOT NULL,
    "dialog_id" UUID NOT NULL,
    "stage" "DialogStage" NOT NULL,
    "payload" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "dialog_states_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "messages" (
    "id" UUID NOT NULL,
    "dialog_id" UUID NOT NULL,
    "role" "MessageRole" NOT NULL,
    "content" TEXT NOT NULL,
    "metadata" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "messages_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "bookings" (
    "id" UUID NOT NULL,
    "client_id" UUID NOT NULL,
    "service" TEXT NOT NULL,
    "datetime" TIMESTAMP(3) NOT NULL,
    "status" "BookingStatus" NOT NULL,
    "notes" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "deleted_at" TIMESTAMP(3),

    CONSTRAINT "bookings_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "scenarios_code_key" ON "scenarios"("code");

CREATE INDEX "dialogs_client_id_idx" ON "dialogs"("client_id");

CREATE INDEX "dialog_states_dialog_id_created_at_idx" ON "dialog_states"("dialog_id", "created_at");

CREATE INDEX "messages_dialog_id_idx" ON "messages"("dialog_id");

CREATE INDEX "bookings_client_id_idx" ON "bookings"("client_id");

CREATE INDEX "bookings_datetime_idx" ON "bookings"("datetime");

ALTER TABLE "dialogs" ADD CONSTRAINT "dialogs_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE "dialogs" ADD CONSTRAINT "dialogs_scenario_id_fkey" FOREIGN KEY ("scenario_id") REFERENCES "scenarios"("id") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "dialog_states" ADD CONSTRAINT "dialog_states_dialog_id_fkey" FOREIGN KEY ("dialog_id") REFERENCES "dialogs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "messages" ADD CONSTRAINT "messages_dialog_id_fkey" FOREIGN KEY ("dialog_id") REFERENCES "dialogs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "bookings" ADD CONSTRAINT "bookings_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "clients"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

INSERT INTO "scenarios" ("id", "code", "name", "is_active", "created_at", "updated_at")
VALUES
  (gen_random_uuid(), 'HAIR_COLORING'::"ScenarioCode", 'Hair coloring', true, NOW(), NOW()),
  (gen_random_uuid(), 'HAIRCUT'::"ScenarioCode", 'Haircut', true, NOW(), NOW()),
  (gen_random_uuid(), 'BROWS'::"ScenarioCode", 'Brows', true, NOW(), NOW()),
  (gen_random_uuid(), 'MAKEUP'::"ScenarioCode", 'Makeup', true, NOW(), NOW()),
  (gen_random_uuid(), 'RETENTION_CAMPAIGN'::"ScenarioCode", 'Retention campaign', true, NOW(), NOW());
