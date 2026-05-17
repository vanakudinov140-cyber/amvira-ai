import { apiClient } from "./client";
import type {
  MessageActionResponse,
  MessageItem,
  MessageStatus,
  MessageVersionsResponse,
  AutomationSettings,
  ModerationInsights,
  AiPerformance,
  ModerationQueueResponse,
  RetentionOverview,
  SchedulerStatus,
  SendPendingResponse,
} from "@/types/api";

export async function fetchRetentionOverview(): Promise<RetentionOverview> {
  const { data } = await apiClient.get<RetentionOverview>(
    "/analytics/retention-overview",
  );
  return data;
}

export async function fetchSchedulerStatus(): Promise<SchedulerStatus> {
  const { data } = await apiClient.get<SchedulerStatus>(
    "/analytics/scheduler-status",
  );
  return data;
}

export async function fetchModerationQueue(params: {
  status?: MessageStatus;
  limit?: number;
  offset?: number;
}): Promise<ModerationQueueResponse> {
  const { data } = await apiClient.get<ModerationQueueResponse>(
    "/messages/moderation-queue",
    { params },
  );
  return data;
}

export async function approveMessage(id: number): Promise<MessageItem> {
  const { data } = await apiClient.post<MessageActionResponse>(
    `/messages/${id}/approve`,
  );
  return data.message;
}

export async function rejectMessage(id: number): Promise<MessageItem> {
  const { data } = await apiClient.post<MessageActionResponse>(
    `/messages/${id}/reject`,
  );
  return data.message;
}

export async function bulkApproveMessages(ids: number[]): Promise<MessageItem[]> {
  return Promise.all(ids.map(approveMessage));
}

export async function bulkRejectMessages(ids: number[]): Promise<MessageItem[]> {
  return Promise.all(ids.map(rejectMessage));
}

export async function updateMessageText(
  id: number,
  text: string,
): Promise<MessageItem> {
  const { data } = await apiClient.patch<MessageActionResponse>(
    `/messages/${id}`,
    { text },
  );
  return data.message;
}

export async function regenerateMessage(id: number): Promise<MessageItem> {
  const { data } = await apiClient.post<MessageActionResponse>(
    `/messages/${id}/regenerate`,
  );
  return data.message;
}

export async function fetchMessageVersions(
  id: number,
  limit = 20,
): Promise<MessageVersionsResponse> {
  const { data } = await apiClient.get<MessageVersionsResponse>(
    `/messages/${id}/versions`,
    { params: { limit } },
  );
  return data;
}

export async function sendApprovedMessages(): Promise<SendPendingResponse> {
  const { data } = await apiClient.post<SendPendingResponse>(
    "/messages/send-pending",
  );
  return data;
}

export async function fetchAutomationSettings(): Promise<AutomationSettings> {
  const { data } = await apiClient.get<AutomationSettings>("/analytics/automation");
  return data;
}

export async function fetchModerationInsights(): Promise<ModerationInsights> {
  const { data } = await apiClient.get<ModerationInsights>(
    "/analytics/moderation-insights",
  );
  return data;
}

export async function toggleSchedulerAutomation(enabled: boolean): Promise<void> {
  await apiClient.post("/scheduler/toggle", { enabled });
}

export async function runSchedulerNow(): Promise<void> {
  await apiClient.post("/scheduler/run-now");
}

export async function fetchAiPerformance(): Promise<AiPerformance> {
  const { data } = await apiClient.get<AiPerformance>("/analytics/ai-performance");
  return data;
}
