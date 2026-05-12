import type { OperatorCommandEnvelopeV1 } from '../operator-contracts/operator-command.contract';
import type { OperatorInterventionKindV1 } from '../operator-contracts/operator-intervention.contract';
import type {
  OperatorAuditLineV1,
  OperatorAuditSnapshotV1,
} from './operator-audit-snapshot.contract';

function interventionForCommandKind(
  kind: OperatorCommandEnvelopeV1['command']['kind'],
): OperatorInterventionKindV1 {
  switch (kind) {
    case 'operator.reply':
      return 'reply';
    case 'takeover.activate':
    case 'takeover.deactivate':
      return 'takeover';
    case 'escalation.resolve':
      return 'escalation';
    case 'dialog.stage.transition':
      return 'stage_transition';
    case 'assistant.resume_signal':
      return 'suppression_signal';
    case 'assistant.override_ack':
      return 'override_ack';
  }
}

export function buildOperatorAuditSnapshot(input: {
  readonly envelope: OperatorCommandEnvelopeV1;
  readonly outcomeStatus: 'completed' | 'rejected' | 'failed';
  readonly lines: readonly OperatorAuditLineV1[];
}): OperatorAuditSnapshotV1 {
  const recordedAt = new Date().toISOString();
  return {
    auditVersion: 'operator_audit_snapshot@v1',
    recordedAt,
    dialogId: input.envelope.dialogId,
    correlationId: input.envelope.correlationId,
    commandKind: input.envelope.command.kind,
    interventionKind: interventionForCommandKind(input.envelope.command.kind),
    outcomeStatus: input.outcomeStatus,
    lines: [...input.lines],
  };
}

export function singleAuditLine(
  tag: string,
  detail: string,
): OperatorAuditLineV1 {
  return { lineVersion: 'operator_audit_line@v1', tag, detail };
}
