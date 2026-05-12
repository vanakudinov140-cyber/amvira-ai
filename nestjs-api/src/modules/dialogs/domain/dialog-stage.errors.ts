import type { DialogStageCode } from './dialog-stage.types';

export type DialogStageTransitionViolationCode =
  | 'UNKNOWN_STAGE'
  | 'COMPLETED_ENTRY_FORBIDDEN'
  | 'INVALID_MONOTONIC_TRANSITION';

/**
 * Pure domain error: no HTTP semantics. Mapped in DialogsService to BadRequestException.
 */
export class DialogStageTransitionDenied extends Error {
  constructor(
    message: string,
    public readonly code: DialogStageTransitionViolationCode,
    public readonly from: DialogStageCode,
    public readonly to: DialogStageCode,
  ) {
    super(message);
    this.name = 'DialogStageTransitionDenied';
  }
}
