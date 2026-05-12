export class ConversationOrchestrationBlockedError extends Error {
  constructor(
    message: string,
    public readonly code: 'dialog_closed' | 'dialog_not_found',
  ) {
    super(message);
    this.name = 'ConversationOrchestrationBlockedError';
  }
}

export type DialogInboundGuardSnapshot = {
  readonly status: string;
};

export function assertDialogAllowsInboundUserMessage(
  dialog: DialogInboundGuardSnapshot,
): void {
  if (dialog.status === 'CLOSED') {
    throw new ConversationOrchestrationBlockedError(
      'Dialog is closed',
      'dialog_closed',
    );
  }
}
