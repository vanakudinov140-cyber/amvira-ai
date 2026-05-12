import type { EscalationReasonCode } from './escalation-reasons.taxonomy';

/**
 * Shape of an escalation queue item — persistence is out of scope; this is the contract only.
 */
export type EscalationQueueItemV1 = {
  readonly itemVersion: 'escalation_queue_item@v1';
  readonly dialogId: string;
  readonly correlationId?: string;
  readonly reasonCode: EscalationReasonCode;
  readonly priority: 'low' | 'medium' | 'high' | 'critical';
  readonly enqueuedAt: string;
  readonly payload: Readonly<Record<string, unknown>>;
};
