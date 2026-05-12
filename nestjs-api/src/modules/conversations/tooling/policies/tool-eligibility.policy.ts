import type { DialogStageCode } from '../../../dialogs/domain/dialog-stage.types';
import { isDialogStageCode } from '../../../dialogs/domain/dialog-stage.types';
import type { SalesToolId } from '../contracts/tool-intent.contract';

const BOOKING_CREATE: readonly DialogStageCode[] = [
  'DISCOVERY',
  'PRESENTATION',
  'OBJECTION_HANDLING',
  'BOOKING',
];

const FOLLOW_UP: readonly DialogStageCode[] = [
  'TRUST_BUILDING',
  'DISCOVERY',
  'PRESENTATION',
  'OBJECTION_HANDLING',
  'BOOKING',
];

export function isToolEligibleForStage(
  toolId: SalesToolId,
  stage: string,
): boolean {
  if (!isDialogStageCode(stage)) {
    return false;
  }
  const s = stage as DialogStageCode;
  if (toolId === 'booking.create_request') {
    return BOOKING_CREATE.includes(s);
  }
  if (toolId === 'follow_up.schedule_contract') {
    return FOLLOW_UP.includes(s);
  }
  if (toolId === 'sales.escalation_handoff') {
    return true;
  }
  return false;
}
