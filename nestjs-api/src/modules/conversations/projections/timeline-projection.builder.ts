import { Injectable } from '@nestjs/common';
import type { Dialog, Message } from '@prisma/client';
import type { ConversationTimelineSnapshotV1 } from '../read-models/conversation-timeline-snapshot.read-model';
import {
  assembleDialogSnapshotTimelineEvent,
  assembleMessageTimelineEvent,
} from '../timeline/conversation-activity-feed.assembler';

/**
 * Builds immutable timeline snapshots from persisted dialog + messages (read path only).
 */
@Injectable()
export class TimelineProjectionBuilder {
  buildSnapshot(
    dialog: Dialog,
    messages: readonly Message[],
  ): ConversationTimelineSnapshotV1 {
    const composedAt = new Date().toISOString();
    const messageEvents = messages.map((m) => assembleMessageTimelineEvent(m));
    const tail = assembleDialogSnapshotTimelineEvent(dialog, composedAt);
    return {
      snapshotVersion: 'conversation_timeline@v1',
      dialogId: dialog.id,
      composedAt,
      events: [...messageEvents, tail],
    };
  }
}
