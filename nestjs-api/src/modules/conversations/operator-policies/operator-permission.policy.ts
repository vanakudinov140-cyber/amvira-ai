import type {
  OperatorAuthorizationContextV1,
  OperatorPermissionV1,
} from '../operator-contracts/operator-permissions.contract';
import type { OperatorCommandKindV1 } from '../operator-contracts/operator-command.contract';

const KIND_TO_PERMISSION: Record<
  OperatorCommandKindV1,
  OperatorPermissionV1
> = {
  'operator.reply': 'dialog:reply',
  'takeover.activate': 'takeover:signal',
  'takeover.deactivate': 'takeover:signal',
  'escalation.resolve': 'escalation:resolve',
  'assistant.resume_signal': 'takeover:signal',
  'assistant.override_ack': 'assistant:override_ack',
  'dialog.stage.transition': 'dialog:stage_transition',
};

export function assertOperatorCommandAuthorized(
  kind: OperatorCommandKindV1,
  authorization?: OperatorAuthorizationContextV1,
):
  | { ok: true }
  | { ok: false; code: 'forbidden'; detail: string } {
  if (!authorization) {
    return { ok: true };
  }
  const need = KIND_TO_PERMISSION[kind];
  if (authorization.granted.includes(need)) {
    return { ok: true };
  }
  return {
    ok: false,
    code: 'forbidden',
    detail: `missing_permission:${need}`,
  };
}
