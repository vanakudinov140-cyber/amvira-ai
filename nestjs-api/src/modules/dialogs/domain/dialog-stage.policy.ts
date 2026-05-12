import { DialogStageTransitionDenied } from './dialog-stage.errors';
import {
  type DialogStageCode,
  DIALOG_STAGE_ORDER,
} from './dialog-stage.types';

function stageIndex(stage: DialogStageCode): number {
  return DIALOG_STAGE_ORDER.indexOf(stage);
}

/**
 * Single transition evaluation (the "matrix" lives here: order + COMPLETED rule).
 *
 * Allowed (non-identity; identity is short-circuited in DialogsService):
 * - Forward along DIALOG_STAGE_ORDER: index(to) > index(from), except when `to` is COMPLETED.
 * - Into COMPLETED only from BOOKING or from COMPLETED (second case is normally not reached).
 *
 * Explicitly forbidden (non-exhaustive wording for operators):
 * - Any stage not present in DIALOG_STAGE_ORDER (unknown).
 * - Backward or same-index lateral move along the backbone when `to` is not COMPLETED.
 * - Into COMPLETED from any stage other than BOOKING or COMPLETED.
 * - No implicit jumps into arbitrary stages except those satisfying the rules above (no hidden defaults).
 */
export function evaluateStageTransition(
  from: DialogStageCode,
  to: DialogStageCode,
): DialogStageTransitionDenied | null {
  if (from === to) {
    return null;
  }

  const fi = stageIndex(from);
  const ti = stageIndex(to);

  if (fi === -1 || ti === -1) {
    return new DialogStageTransitionDenied(
      'Unknown dialog stage',
      'UNKNOWN_STAGE',
      from,
      to,
    );
  }

  if (to === 'COMPLETED') {
    if (from !== 'BOOKING' && from !== 'COMPLETED') {
      return new DialogStageTransitionDenied(
        'COMPLETED is only allowed after BOOKING',
        'COMPLETED_ENTRY_FORBIDDEN',
        from,
        to,
      );
    }
    return null;
  }

  if (ti <= fi) {
    return new DialogStageTransitionDenied(
      'Invalid stage transition',
      'INVALID_MONOTONIC_TRANSITION',
      from,
      to,
    );
  }

  return null;
}

export function assertStageTransitionAllowed(
  from: DialogStageCode,
  to: DialogStageCode,
): void {
  const denied = evaluateStageTransition(from, to);
  if (denied) {
    throw denied;
  }
}
