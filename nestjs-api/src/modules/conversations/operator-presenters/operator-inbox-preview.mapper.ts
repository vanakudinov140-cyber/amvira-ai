import type { OperationsEnvelopeV1 } from '../operations/contracts/operations-envelope.contract';
import type { OperatorInboxQueryInput } from '../inbox/operator-inbox-query.input';

export function mapInboxPreviewContext(
  raw?: Readonly<Record<string, Readonly<Record<string, unknown>>>>,
):
  | Readonly<
      Partial<
        Record<
          string,
          Pick<
            OperatorInboxQueryInput,
            'workspaceSignals' | 'lastOperationsEnvelope'
          >
        >
      >
    >
  | undefined {
  if (!raw) {
    return undefined;
  }
  const out: Partial<
    Record<
      string,
      Pick<OperatorInboxQueryInput, 'workspaceSignals' | 'lastOperationsEnvelope'>
    >
  > = {};
  for (const [dialogId, ctx] of Object.entries(raw)) {
    const ws = ctx.workspaceSignals as
      | { takeoverActive?: boolean }
      | undefined;
    const env = ctx.lastOperationsEnvelope as unknown as
      | OperationsEnvelopeV1
      | undefined;
    out[dialogId] = {
      workspaceSignals: ws,
      lastOperationsEnvelope: env,
    };
  }
  return out;
}
