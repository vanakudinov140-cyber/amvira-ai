export interface SyncResponse {
  success?: boolean;
  synced: number;
}

export interface RetentionCandidate {
  client_id: number;
  client_name: string;
  procedure_name: string;
  last_visit_date: string;
  days_since_visit: number;
  recommended_action: string;
  recommended_channel: string;
}

export interface RetentionCandidatesResponse {
  count: number;
  items: RetentionCandidate[];
}

export interface PendingMessagesResponse {
  items: MessageItem[];
}

export type MessageStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "sent"
  | "failed";

export interface RetentionOverview {
  clients_total: number;
  retention_candidates: number;
  messages_pending: number;
  messages_approved: number;
  messages_rejected: number;
  messages_sent: number;
  messages_failed: number;
  daily_sent: number;
  actions_breakdown: {
    monthly_care: number;
    gentle_return: number;
    comeback_reminder: number;
    winback: number;
  };
}

export interface SchedulerStatus {
  scheduler_running: boolean;
  last_job_started_at: string | null;
  last_job_finished_at: string | null;
  last_job_status: string | null;
  last_job_error: string | null;
}

export type ClientSegment = "new" | "active" | "loyal" | "sleeping" | "lost_vip";

export interface MessageMetadata {
  days_since_last_visit: number;
  previous_visit_frequency_days: number | null;
  average_check?: number;
  visit_count?: number;
  client_segment: ClientSegment | string;
  client_segment_label?: string;
  trigger_reason: string;
  trigger_reason_label?: string;
  predicted_return_probability: number;
  recommended_action: string;
  recommended_action_label?: string;
}

export interface MessageItem {
  id: number;
  client_id: number;
  text: string;
  channel: string;
  action: string;
  status: MessageStatus;
  prepared_at: string;
  sent_at: string | null;
  metadata: MessageMetadata | null;
  explain: string[];
}

export interface ModerationQueueResponse {
  items: MessageItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface MessageActionResponse {
  success: boolean;
  message: MessageItem;
}

export interface SendPendingResponse {
  success: boolean;
  sent: number;
  failed: number;
}

export type MessageVersionSource = "ai" | "manual" | "regenerate";

export interface MessageVersionItem {
  id: number;
  message_id: number;
  old_content: string;
  new_content: string;
  source: MessageVersionSource;
  created_at: string;
}

export interface MessageVersionsResponse {
  items: MessageVersionItem[];
}

export interface AutomationSettings {
  scheduler_running: boolean;
  automation_enabled: boolean;
  test_mode: boolean;
  test_recipients: string[];
  send_pending_limit: number;
  daily_send_limit: number;
  quiet_hours_start: number;
  quiet_hours_end: number;
  last_job_started_at: string | null;
  last_job_finished_at: string | null;
  last_job_status: string | null;
  last_job_error: string | null;
}

export interface AiPerformance {
  approval_rate: number;
  average_edit_ratio: number;
  messages_sent: number;
  messages_returned: number;
  overall_return_rate: number;
  retention_revenue: number;
  top_performing_actions: {
    action: string;
    sent: number;
    returned: number;
    return_rate: number;
    revenue: number;
  }[];
  top_performing_segments: {
    segment: string;
    sent: number;
    returned: number;
    return_rate: number;
  }[];
  return_rate_by_action: Record<string, number>;
  return_rate_by_segment: Record<string, number>;
  edited_vs_original: {
    edited_sent: number;
    edited_returned: number;
    edited_return_rate: number;
    non_edited_sent: number;
    non_edited_returned: number;
    non_edited_return_rate: number;
  };
  regenerated_vs_original: {
    regenerated_sent: number;
    regenerated_returned: number;
    regenerated_return_rate: number;
    original_sent: number;
    original_returned: number;
    original_return_rate: number;
  };
  learning_recommendations: string[];
}

export interface ModerationInsights {
  messages_by_segment: Record<string, number>;
  return_rate_by_segment: Record<string, number>;
  top_performing_actions: { action: string; sent: number; total: number }[];
  ai_moderation: {
    approved: number;
    rejected: number;
    pending: number;
  };
}
