import { assertStageTransitionAllowed } from '../../dialogs/domain/dialog-stage.policy';
import { DialogStageTransitionDenied } from '../../dialogs/domain/dialog-stage.errors';
import { isDialogStageCode } from '../../dialogs/domain/dialog-stage.types';
import type { EscalationResolutionCodeV1 } from '../operator-contracts/escalation-resolution.contract';
import { ESCALATION_RESOLUTION_CODES } from '../operator-contracts/escalation-resolution.contract';
import type {
  OperatorCommandEnvelopeV1,
  OperatorReplyCommandPayloadV1,
  OperatorStageTransitionCommandPayloadV1,
} from '../operator-contracts/operator-command.contract';

export type OperatorValidationDialogSnapshot = {
  readonly currentStage: string;
  readonly status: string;
};

export type OperatorCommandValidationResult =
  | { ok: true }
  | { ok: false; code: string; detail?: string };

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function parseReplyPayload(
  payload: Readonly<Record<string, unknown>>,
): OperatorReplyCommandPayloadV1 | null {
  if (!isRecord(payload)) {
    return null;
  }
  const body = payload.body;
  if (typeof body !== 'string' || body.length < 1 || body.length > 32000) {
    return null;
  }
  const operatorLabel = payload.operatorLabel;
  if (
    operatorLabel !== undefined &&
    typeof operatorLabel !== 'string'
  ) {
    return null;
  }
  return { body, operatorLabel };
}

function parseStagePayload(
  payload: Readonly<Record<string, unknown>>,
): OperatorStageTransitionCommandPayloadV1 | null {
  if (!isRecord(payload)) {
    return null;
  }
  const targetStage = payload.targetStage;
  if (typeof targetStage !== 'string') {
    return null;
  }
  const workflowPayload = payload.workflowPayload;
  if (
    workflowPayload !== undefined &&
    (!isRecord(workflowPayload) || Array.isArray(workflowPayload))
  ) {
    return null;
  }
  return {
    targetStage,
    workflowPayload: workflowPayload as
      | Readonly<Record<string, unknown>>
      | undefined,
  };
}

function parseEscalationPayload(
  payload: Readonly<Record<string, unknown>>,
): { resolutionCode: EscalationResolutionCodeV1; note?: string } | null {
  if (!isRecord(payload)) {
    return null;
  }
  const code = payload.resolutionCode;
  if (
    typeof code !== 'string' ||
    !(ESCALATION_RESOLUTION_CODES as readonly string[]).includes(code)
  ) {
    return null;
  }
  const note = payload.note;
  if (note !== undefined && typeof note !== 'string') {
    return null;
  }
  return { resolutionCode: code as EscalationResolutionCodeV1, note };
}

export function validateOperatorCommandExecution(input: {
  readonly envelope: OperatorCommandEnvelopeV1;
  readonly dialog: OperatorValidationDialogSnapshot;
}): OperatorCommandValidationResult & {
  parsedReply?: OperatorReplyCommandPayloadV1;
  parsedStage?: OperatorStageTransitionCommandPayloadV1;
  parsedEscalation?: { resolutionCode: EscalationResolutionCodeV1; note?: string };
} {
  const { envelope, dialog } = input;
  if (dialog.status === 'CLOSED') {
    return { ok: false, code: 'dialog_closed', detail: 'dialog_is_closed' };
  }

  switch (envelope.command.kind) {
    case 'operator.reply': {
      const parsed = parseReplyPayload(envelope.command.payload);
      if (!parsed) {
        return { ok: false, code: 'invalid_payload', detail: 'reply.body' };
      }
      return { ok: true, parsedReply: parsed };
    }
    case 'dialog.stage.transition': {
      const parsed = parseStagePayload(envelope.command.payload);
      if (!parsed) {
        return {
          ok: false,
          code: 'invalid_payload',
          detail: 'stage.targetStage',
        };
      }
      const from = dialog.currentStage;
      const to = parsed.targetStage;
      if (!isDialogStageCode(from) || !isDialogStageCode(to)) {
        return { ok: false, code: 'invalid_stage_code', detail: `${from}->${to}` };
      }
      try {
        assertStageTransitionAllowed(from, to);
      } catch (e) {
        if (e instanceof DialogStageTransitionDenied) {
          return { ok: false, code: 'stage_transition_denied', detail: e.message };
        }
        throw e;
      }
      return { ok: true, parsedStage: parsed };
    }
    case 'escalation.resolve': {
      const parsed = parseEscalationPayload(envelope.command.payload);
      if (!parsed) {
        return {
          ok: false,
          code: 'invalid_payload',
          detail: 'escalation.resolutionCode',
        };
      }
      return { ok: true, parsedEscalation: parsed };
    }
    case 'takeover.activate':
    case 'takeover.deactivate':
    case 'assistant.resume_signal':
    case 'assistant.override_ack':
      return { ok: true };
  }
}
