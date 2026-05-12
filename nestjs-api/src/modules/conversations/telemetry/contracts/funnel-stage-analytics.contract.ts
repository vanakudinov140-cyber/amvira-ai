/**
 * Funnel position snapshot for analytics — not an FSM transition proposal.
 */
export type FunnelStageAnalyticsV1 = {
  readonly funnelVersion: 'funnel_stage_analytics@v1';
  readonly dialogStageCode: string;
  readonly dialogStatus: string;
  readonly channel?: string;
};
