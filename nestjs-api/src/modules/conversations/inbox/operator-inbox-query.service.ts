import { Injectable } from '@nestjs/common';
import type { Dialog, Message } from '@prisma/client';
import { DialogsService } from '../../dialogs/dialogs.service';
import { MessagesService } from '../../messages/messages.service';
import { TimelineProjectionBuilder } from '../projections/timeline-projection.builder';
import type { ConversationTimelineSnapshotV1 } from '../read-models/conversation-timeline-snapshot.read-model';
import type { OperatorInboxRowV1 } from '../read-models/operator-inbox-row.read-model';
import type { OperatorInboxUnreadSignalsV1 } from '../read-models/operator-inbox-unread-signals.read-model';
import type { AiVisibilitySnapshotV1 } from '../read-models/visibility/ai-visibility-snapshot.read-model';
import type { DeliveryVisibilitySnapshotV1 } from '../read-models/visibility/delivery-visibility-snapshot.read-model';
import type { EscalationVisibilityV1 } from '../read-models/visibility/escalation-visibility.read-model';
import type { HandoffTakeoverVisibilityV1 } from '../read-models/visibility/handoff-takeover-visibility.read-model';
import type { ToolExecutionVisibilitySnapshotV1 } from '../read-models/visibility/tool-execution-visibility-snapshot.read-model';
import type { OperatorInboxQueryInput } from './operator-inbox-query.input';

@Injectable()
export class OperatorInboxQueryService {
  constructor(
    private readonly dialogs: DialogsService,
    private readonly messages: MessagesService,
    private readonly timelineProjection: TimelineProjectionBuilder,
  ) {}

  async getInboxRow(input: OperatorInboxQueryInput): Promise<OperatorInboxRowV1> {
    const dialog = await this.dialogs.findOne(input.dialogId);
    const messages = await this.messages.listByDialog(input.dialogId);
    const timeline = this.timelineProjection.buildSnapshot(dialog, messages);
    return this.composeRow(dialog, messages, timeline, input);
  }

  async previewRows(
    dialogIds: readonly string[],
    contextByDialogId?: Readonly<
      Partial<
        Record<
          string,
          Pick<
            OperatorInboxQueryInput,
            'workspaceSignals' | 'lastOperationsEnvelope'
          >
        >
      >
    >,
  ): Promise<readonly OperatorInboxRowV1[]> {
    return Promise.all(
      dialogIds.map((dialogId) =>
        this.getInboxRow({
          dialogId,
          workspaceSignals: contextByDialogId?.[dialogId]?.workspaceSignals,
          lastOperationsEnvelope:
            contextByDialogId?.[dialogId]?.lastOperationsEnvelope,
        }),
      ),
    );
  }

  private composeRow(
    dialog: Dialog,
    messages: readonly Message[],
    timeline: ConversationTimelineSnapshotV1,
    input: OperatorInboxQueryInput,
  ): OperatorInboxRowV1 {
    const last = messages.length ? messages[messages.length - 1] : undefined;
    const lastAssistant = [...messages]
      .reverse()
      .find((m) => m.role === 'ASSISTANT');
    const toolMessageCount = messages.filter((m) => m.role === 'TOOL').length;

    const unreadSignals: OperatorInboxUnreadSignalsV1 = {
      version: 'operator_inbox_unread@v1',
      lastMessageRole: last?.role,
      suggestedPendingReview: last?.role === 'USER',
    };

    const env = input.lastOperationsEnvelope;
    const handoffTakeover: HandoffTakeoverVisibilityV1 = {
      version: 'handoff_takeover_visibility@v1',
      takeoverActive: input.workspaceSignals?.takeoverActive === true,
      takeoverSource:
        input.workspaceSignals?.takeoverActive !== undefined
          ? 'workspace_signal'
          : 'unknown',
      handoffQueueRoutingActive: env?.handoffDecision?.routeToOperatorQueue === true,
      handoffSource: env ? 'last_operations_envelope' : 'unknown',
    };

    const escalation: EscalationVisibilityV1 = {
      version: 'escalation_visibility@v1',
      escalationIntentPresent: env?.escalationIntent != null,
      queueRoutingConfirmed: env?.handoffDecision?.routeToOperatorQueue === true,
      source: env ? 'last_operations_envelope' : 'unknown',
    };

    const delivery: DeliveryVisibilitySnapshotV1 = {
      version: 'delivery_visibility@v1',
      channel: String(dialog.channel),
      lastMileStatus: 'unknown',
      source: 'dialog_channel_only',
    };

    const aiVisibility: AiVisibilitySnapshotV1 = {
      version: 'ai_health_summary@v1',
      source: 'message_corpus',
      hasAssistantTurn: lastAssistant != null,
      lastAssistantExcerpt: lastAssistant?.content.slice(0, 200),
      lastAssistantAtIso: lastAssistant?.createdAt.toISOString(),
      stalledHint:
        last?.role === 'USER' &&
        lastAssistant != null &&
        last.createdAt.getTime() >= lastAssistant.createdAt.getTime(),
    };

    const toolExecution: ToolExecutionVisibilitySnapshotV1 = {
      version: 'tool_execution_visibility@v1',
      source: 'message_corpus',
      toolMessageCount,
    };

    return {
      rowVersion: 'operator_inbox_row@v1',
      dialogId: dialog.id,
      clientId: dialog.clientId,
      channel: String(dialog.channel),
      currentStage: String(dialog.currentStage),
      dialogStatus: String(dialog.status),
      updatedAtIso: dialog.updatedAt.toISOString(),
      lastMessageAtIso: last?.createdAt.toISOString(),
      unreadSignals,
      handoffTakeover,
      escalation,
      delivery,
      aiVisibility,
      toolExecution,
      timeline,
    };
  }

  async getConversationTimeline(
    dialogId: string,
  ): Promise<ConversationTimelineSnapshotV1> {
    const dialog = await this.dialogs.findOne(dialogId);
    const messages = await this.messages.listByDialog(dialogId);
    return this.timelineProjection.buildSnapshot(dialog, messages);
  }
}
