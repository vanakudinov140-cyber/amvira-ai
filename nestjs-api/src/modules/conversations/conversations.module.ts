import { Module } from '@nestjs/common';
import { AiModule } from '../ai/ai.module';
import { AssistantReplyFallbackBuilder } from '../ai/fallback/assistant-reply-fallback.builder';
import { BookingsModule } from '../bookings/bookings.module';
import { DialogsModule } from '../dialogs/dialogs.module';
import { MessagesModule } from '../messages/messages.module';
import { ConversationOrchestrationLogger } from './orchestration/conversation-orchestration.logging';
import { InMemoryConversationIdempotencyGuard } from './orchestration/conversation-idempotency.guard';
import { ConversationOrchestratorService } from './use-cases/conversation-orchestrator.service';
import { ToolExecutionOrchestrator } from './tooling/execution/tool-execution.orchestrator';
import { BookingCreateRequestExecutor } from './tooling/executors/booking-create-request.executor';
import { EscalationHandoffExecutor } from './tooling/executors/escalation-handoff.executor';
import { FollowUpContractExecutor } from './tooling/executors/follow-up-contract.executor';
import { SalesToolProposalBuilder } from './tooling/proposal/sales-tool-proposal.builder';
import { SalesToolRegistry } from './tooling/registry/sales-tool.registry';
import { OperatorOperationsComposer } from './operations/operator-operations.composer';
import {
  CONVERSATION_TELEMETRY_PUBLISHER,
  LoggerConversationTelemetryPublisher,
} from './telemetry/conversation-telemetry.publisher';
import { TimelineProjectionBuilder } from './projections/timeline-projection.builder';
import { OperatorInboxQueryService } from './inbox/operator-inbox-query.service';
import { OperatorActionOrchestratorService } from './operator-actions/operator-action-orchestrator.service';
import { OperatorActionsController } from './operator-api/operator-actions.controller';
import { OperatorInboxController } from './operator-api/operator-inbox.controller';
import { OperatorTimelineController } from './operator-api/operator-timeline.controller';
import { OperatorApiExceptionFilter } from './operator-http/operator-api-exception.filter';

@Module({
  imports: [DialogsModule, MessagesModule, AiModule, BookingsModule],
  controllers: [
    OperatorInboxController,
    OperatorTimelineController,
    OperatorActionsController,
  ],
  providers: [
    ConversationOrchestrationLogger,
    InMemoryConversationIdempotencyGuard,
    SalesToolProposalBuilder,
    EscalationHandoffExecutor,
    FollowUpContractExecutor,
    BookingCreateRequestExecutor,
    SalesToolRegistry,
    ToolExecutionOrchestrator,
    OperatorOperationsComposer,
    {
      provide: CONVERSATION_TELEMETRY_PUBLISHER,
      useClass: LoggerConversationTelemetryPublisher,
    },
    TimelineProjectionBuilder,
    OperatorInboxQueryService,
    OperatorActionOrchestratorService,
    OperatorApiExceptionFilter,
    AssistantReplyFallbackBuilder,
    ConversationOrchestratorService,
  ],
  exports: [
    ConversationOrchestratorService,
    OperatorInboxQueryService,
    OperatorActionOrchestratorService,
  ],
})
export class ConversationsModule {}
