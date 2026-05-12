import type { OperationsEnvelopeV1 } from '../operations/contracts/operations-envelope.contract';

export type OperatorInboxWorkspaceSignalsV1 = Readonly<{
  readonly takeoverActive?: boolean;
}>;

/**
 * Optional last-turn operations envelope from gateway/session cache — not loaded here.
 */
export type OperatorInboxQueryInput = {
  readonly dialogId: string;
  readonly workspaceSignals?: OperatorInboxWorkspaceSignalsV1;
  readonly lastOperationsEnvelope?: OperationsEnvelopeV1;
};
