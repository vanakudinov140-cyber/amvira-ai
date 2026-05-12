/**
 * AI may only influence routing scores — never set operator takeover or queue ack.
 */
export type AiConfidenceRoutingV1 = {
  readonly routingVersion: 'ai_confidence_routing@v1';
  readonly overallConfidence: number;
  readonly suggestOperatorReview: boolean;
  readonly suggestQueueEscalation: boolean;
  readonly rationale: string;
};
