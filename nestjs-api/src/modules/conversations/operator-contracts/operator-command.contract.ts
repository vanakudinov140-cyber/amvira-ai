import type { OperatorAuthorizationContextV1 } from './operator-permissions.contract';

export const OPERATOR_COMMAND_KINDS = [
  'operator.reply',
  'takeover.activate',
  'takeover.deactivate',
  'escalation.resolve',
  'assistant.resume_signal',
  'assistant.override_ack',
  'dialog.stage.transition',
] as const;

export type OperatorCommandKindV1 = (typeof OPERATOR_COMMAND_KINDS)[number];

export type OperatorReplyCommandPayloadV1 = {
  readonly body: string;
  readonly operatorLabel?: string;
};

export type OperatorStageTransitionCommandPayloadV1 = {
  readonly targetStage: string;
  readonly workflowPayload?: Readonly<Record<string, unknown>>;
};

export type OperatorCommandV1 = {
  readonly commandVersion: 'operator_command@v1';
  readonly kind: OperatorCommandKindV1;
  readonly payload: Readonly<Record<string, unknown>>;
};

export type OperatorCommandEnvelopeV1 = {
  readonly envelopeVersion: 'operator_command_envelope@v1';
  readonly dialogId: string;
  readonly correlationId?: string;
  readonly command: OperatorCommandV1;
  readonly authorization?: OperatorAuthorizationContextV1;
  readonly actor?: Readonly<{
    readonly operatorId?: string;
    readonly label?: string;
  }>;
};
