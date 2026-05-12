import { Inject, Injectable, NotFoundException } from '@nestjs/common';
import { MessageRole, type Dialog } from '@prisma/client';
import { performance } from 'node:perf_hooks';
import { randomUUID } from 'node:crypto';
import type { AiGenerationRequest } from '../../ai/contracts/ai-generation.request';
import { AiOrchestrationService } from '../../ai/orchestration/ai-orchestration.service';
import { AiSalesDecisionService } from '../../ai/sales-decisions/ai-sales-decision.service';
import type { ChannelAdapter } from '../../channels/channel-adapter.contract';
import { CHANNEL_ADAPTER } from '../../channels/channel-adapter.contract';
import { DialogsService } from '../../dialogs/dialogs.service';
import { CreateMessageDto } from '../../messages/dto/create-message.dto';
import { MessagesService } from '../../messages/messages.service';
import type { AsyncJobDispatcher } from '../../../shared/async/async-job-dispatcher.contract';
import { ASYNC_JOB_DISPATCHER } from '../../../shared/async/async-job-dispatcher.contract';
import type { AssistantReplyCandidate } from '../contracts/assistant-reply-candidate';
import type { UserMessageOrchestrationRequest } from '../contracts/user-message-orchestration.request';
import type { AssistantReplyQualityReportV1 } from '../../ai/quality/assistant-reply-quality.evaluator';
import { evaluateAssistantReplyQuality } from '../../ai/quality/assistant-reply-quality.evaluator';
import { AssistantReplyFallbackBuilder } from '../../ai/fallback/assistant-reply-fallback.builder';
import {
  ASSISTANT_REPLY_SCHEMA_ID,
  ASSISTANT_REPLY_SCHEMA_VERSION,
} from '../../ai/contracts/structured-output.contract';
import { ToolExecutionOrchestrator } from '../tooling/execution/tool-execution.orchestrator';
import { SalesToolProposalBuilder } from '../tooling/proposal/sales-tool-proposal.builder';
import {
  classifyOrchestrationFailure,
  ConversationAiTimeoutError,
} from '../orchestration/conversation-orchestration.errors';
import { InMemoryConversationIdempotencyGuard } from '../orchestration/conversation-idempotency.guard';
import { ConversationOrchestrationLogger } from '../orchestration/conversation-orchestration.logging';
import type {
  ConversationDeliveryOutcome,
  ConversationOrchestrationResult,
  ConversationOrchestrationStatus,
} from '../orchestration/conversation-orchestration.result';
import {
  CONVERSATION_AI_SUGGEST_TIMEOUT_MS,
  withConversationTimeout,
} from '../orchestration/conversation-timeout.policy';
import {
  assertDialogAllowsInboundUserMessage,
  ConversationOrchestrationBlockedError,
} from '../orchestration/guards/conversation-orchestration.guards';
import { OperatorOperationsComposer } from '../operations/operator-operations.composer';
import {
  CONVERSATION_TELEMETRY_PUBLISHER,
  type ConversationTelemetryPublisher,
} from '../telemetry/conversation-telemetry.publisher';
import {
  buildOrchestrationTelemetrySnapshot,
  buildOrchestrationTelemetryStructuredEvent,
} from '../telemetry/orchestration-telemetry.builder';
import { OrchestrationTimingCollector } from '../telemetry/orchestration-timing.collector';

/**
 * Production-oriented orchestration boundary: structured logs, correlation,
 * in-process idempotency, AI wall-clock timeout, normalized delivery outcomes.
 */
@Injectable()
export class ConversationOrchestratorService {
  constructor(
    private readonly dialogs: DialogsService,
    private readonly messages: MessagesService,
    private readonly ai: AiOrchestrationService,
    private readonly salesDecision: AiSalesDecisionService,
    private readonly toolProposalBuilder: SalesToolProposalBuilder,
    private readonly toolExecutionOrchestrator: ToolExecutionOrchestrator,
    private readonly operatorOperations: OperatorOperationsComposer,
    @Inject(CHANNEL_ADAPTER) private readonly channel: ChannelAdapter,
    @Inject(ASYNC_JOB_DISPATCHER) private readonly asyncJobs: AsyncJobDispatcher,
    private readonly orchLog: ConversationOrchestrationLogger,
    private readonly idempotency: InMemoryConversationIdempotencyGuard,
    private readonly aiFallback: AssistantReplyFallbackBuilder,
    @Inject(CONVERSATION_TELEMETRY_PUBLISHER)
    private readonly telemetryPublisher: ConversationTelemetryPublisher,
  ) {}

  async handleUserMessage(
    request: UserMessageOrchestrationRequest,
  ): Promise<ConversationOrchestrationResult> {
    const baseLog = {
      correlationId: request.correlationId,
      dialogId: request.dialogId,
    };

    if (request.turnIdempotencyKey) {
      const turnKey = this.idempotency.buildTurnKey(
        request.dialogId,
        request.turnIdempotencyKey,
      );
      const cached = this.idempotency.getCached(turnKey);
      if (cached) {
        this.orchLog.logStructured('idempotency_hit', {
          ...baseLog,
          turnKey,
        });
        const replay: ConversationOrchestrationResult = {
          ...cached,
          correlationId: request.correlationId ?? cached.correlationId,
        };
        const timing = new OrchestrationTimingCollector();
        timing.mark('idempotency_hit');
        this.emitTurnTelemetry(
          timing,
          request,
          undefined,
          replay,
          'orchestration.idempotency_hit',
          replay.toolExecution != null,
        );
        return replay;
      }
    }

    const result = await this.runTurn(request, baseLog);

    if (request.turnIdempotencyKey) {
      const turnKey = this.idempotency.buildTurnKey(
        request.dialogId,
        request.turnIdempotencyKey,
      );
      this.idempotency.remember(turnKey, result);
    }

    return result;
  }

  private async runTurn(
    request: UserMessageOrchestrationRequest,
    baseLog: { correlationId?: string; dialogId: string },
  ): Promise<ConversationOrchestrationResult> {
    const persistAssistant = request.persistAssistantMessage !== false;
    const dispatch = request.dispatchToChannel === true;
    const deferDispatch = request.deferChannelDispatch === true;

    const timing = new OrchestrationTimingCollector();
    timing.mark('turn_start');

    this.orchLog.logStructured('start', baseLog);

    let dialog: Dialog | undefined;
    try {
      dialog = await this.dialogs.findOne(request.dialogId);
      this.orchLog.logStructured('dialog_loaded', baseLog);
      timing.mark('dialog_loaded');
    } catch (e) {
      if (e instanceof NotFoundException) {
        this.orchLog.warnStructured('dialog_loaded', {
          ...baseLog,
          outcome: 'not_found',
        });
        const blocked: ConversationOrchestrationResult = {
          status: 'blocked_dialog_not_found',
          dialogId: request.dialogId,
          correlationId: request.correlationId,
          recoverability: 'non_recoverable',
        };
        this.emitTurnTelemetry(
          timing,
          request,
          undefined,
          blocked,
          'orchestration.turn_snapshot',
          request.executeTools === true,
        );
        return blocked;
      }
      throw e;
    }

    try {
      assertDialogAllowsInboundUserMessage(dialog);
      this.orchLog.logStructured('dialog_guard', { ...baseLog, outcome: 'ok' });
    } catch (e) {
      if (e instanceof ConversationOrchestrationBlockedError) {
        this.orchLog.warnStructured('dialog_guard', {
          ...baseLog,
          outcome: 'blocked',
          code: e.code,
        });
        const blocked: ConversationOrchestrationResult = {
          status: 'blocked_dialog',
          dialogId: request.dialogId,
          correlationId: request.correlationId,
          recoverability: 'non_recoverable',
        };
        this.emitTurnTelemetry(
          timing,
          request,
          dialog,
          blocked,
          'orchestration.turn_snapshot',
          request.executeTools === true,
        );
        return blocked;
      }
      throw e;
    }

    let userMessage;
    try {
      const dto: CreateMessageDto = {
        role: MessageRole.USER,
        content: request.userText,
      } as CreateMessageDto;
      userMessage = await this.messages.createForDialog(request.dialogId, dto);
      this.orchLog.logStructured('user_persist', {
        ...baseLog,
        userMessageId: userMessage.id,
      });
      timing.mark('user_persisted');
    } catch (err) {
      this.orchLog.errorStructured('user_persist', {
        ...baseLog,
        error: err instanceof Error ? err.message : String(err),
      });
      const failed: ConversationOrchestrationResult = {
        status: 'failed_user_message_persist',
        dialogId: request.dialogId,
        correlationId: request.correlationId,
        recoverability: classifyOrchestrationFailure(err),
      };
      this.emitTurnTelemetry(
        timing,
        request,
        dialog,
        failed,
        'orchestration.turn_snapshot',
        request.executeTools === true,
      );
      return failed;
    }

    const scenarioCode = await this.dialogs.getScenarioCodeForDialog(dialog.id);
    const aiRequest: AiGenerationRequest = {
      dialogId: dialog.id,
      correlationId: request.correlationId,
      currentStage: dialog.currentStage,
      dialogStatus: dialog.status,
      channel: dialog.channel,
      scenarioCode: scenarioCode ?? undefined,
      userTurn: { text: request.userText },
    };

    const tAi = performance.now();
    let candidate!: AssistantReplyCandidate;
    let aiReplyMeta: ConversationOrchestrationResult['aiReplyMeta'];
    let traceRefusal: ConversationOrchestrationResult['aiRefusal'];

    const applyFallback = (
      fbReason: 'timeout' | 'refusal' | 'failure' | 'validation',
      prior?: ConversationOrchestrationResult['aiRefusal'],
    ) => {
      const fb = this.aiFallback.build({
        currentStage: dialog.currentStage,
        channel: dialog.channel,
        userText: request.userText,
        reason: fbReason,
      });
      candidate = {
        replyText: fb.replyText,
        structured: { replyText: fb.replyText, refused: false },
        modelId: 'deterministic_fallback',
        schemaId: ASSISTANT_REPLY_SCHEMA_ID,
        schemaVersion: ASSISTANT_REPLY_SCHEMA_VERSION,
      };
      aiReplyMeta = {
        usedFallback: true,
        fallbackReason: fbReason,
        priorFailureReason: prior?.reason,
        priorFailureDetail: prior?.detail,
      };
      traceRefusal = prior;
    };

    try {
      const ai = await withConversationTimeout(
        CONVERSATION_AI_SUGGEST_TIMEOUT_MS,
        request.correlationId,
        () => this.ai.suggest(aiRequest),
      );
      timing.setAiSuggestWallMs(Math.round(performance.now() - tAi));
      timing.mark('ai_suggest_complete');
      this.orchLog.logStructured('ai_suggest', { ...baseLog, outcome: 'ok' });

      if (ai.kind === 'refusal' || ai.kind === 'failure') {
        this.orchLog.warnStructured('ai_suggest', {
          ...baseLog,
          outcome: ai.kind,
          reason: ai.refusal.reason,
        });
        applyFallback(
          ai.kind === 'refusal' ? 'refusal' : 'failure',
          {
            reason: ai.refusal.reason,
            detail: ai.refusal.detail,
          },
        );
      } else {
        const data = ai.structured.data;
        if (!data || typeof data !== 'object') {
          this.orchLog.warnStructured('ai_structured_validate', {
            ...baseLog,
            outcome: 'null_data',
          });
          applyFallback('validation', {
            reason: 'validation.failed',
            detail: 'structured_data_null',
          });
        } else {
          const replyOk =
            typeof data.replyText === 'string' ? data.replyText : '';
          candidate = {
            replyText: replyOk,
            structured: data as Readonly<Record<string, unknown>>,
            modelId: ai.modelId,
            schemaId: ai.structured.schemaId,
            schemaVersion: ai.structured.schemaVersion,
          };
          aiReplyMeta = undefined;
          traceRefusal = undefined;
        }
      }
    } catch (err) {
      if (err instanceof ConversationAiTimeoutError) {
        timing.setAiSuggestWallMs(Math.round(performance.now() - tAi));
        this.orchLog.warnStructured('ai_suggest', {
          ...baseLog,
          outcome: 'timeout',
          limitMs: CONVERSATION_AI_SUGGEST_TIMEOUT_MS,
        });
        applyFallback('timeout', {
          reason: 'ai.timeout',
          detail: String(CONVERSATION_AI_SUGGEST_TIMEOUT_MS),
        });
      } else {
        timing.setAiSuggestWallMs(Math.round(performance.now() - tAi));
        this.orchLog.errorStructured('ai_suggest', {
          ...baseLog,
          error: err instanceof Error ? err.message : String(err),
        });
        applyFallback('failure', {
          reason: 'ai.unexpected_error',
          detail: err instanceof Error ? err.message : String(err),
        });
      }
      timing.mark('ai_suggest_complete');
    }

    const replyText = candidate.replyText;

    const aiSalesDecision = this.salesDecision.compose({
      userText: request.userText,
      assistantReplyText: replyText,
      currentStage: dialog.currentStage,
      dialogStatus: dialog.status,
    });

    const assistantReplyQuality: AssistantReplyQualityReportV1 =
      evaluateAssistantReplyQuality({
        replyText,
        userText: request.userText,
        decision: aiSalesDecision,
      });

    const toolProposals = this.toolProposalBuilder.build({
      dialogId: dialog.id,
      channel: dialog.channel,
      currentStage: dialog.currentStage,
      decision: aiSalesDecision,
    });

    const toolExecution =
      request.executeTools === true
        ? await this.toolExecutionOrchestrator.run(toolProposals, {
            dialogId: dialog.id,
            clientId: dialog.clientId,
            currentStage: dialog.currentStage,
            dialogStatus: dialog.status,
            executeTools: true,
            confirmedIntentIds: new Set(
              request.toolExecutionContext?.confirmedIntentIds ?? [],
            ),
            bookingPayload: request.toolExecutionContext?.bookingPayload,
          })
        : undefined;

    timing.mark('tool_execution_complete');

    const operationsEnvelope = this.operatorOperations.compose({
      dialogId: dialog.id,
      correlationId: request.correlationId,
      dialogStatus: dialog.status,
      decision: aiSalesDecision,
      toolProposals,
      operatorTakeoverActive:
        request.operatorContext?.operatorTakeoverActive === true,
      resumeAssistantRequested:
        request.operatorContext?.resumeAssistantRequested === true,
      confirmEscalationToQueue:
        request.operatorContext?.confirmEscalationToQueue === true,
      assistantReplyQuality,
      userTextForAssist: request.userText,
    });

    timing.mark('operations_envelope_complete');

    this.orchLog.logStructured('ai_structured_validate', {
      ...baseLog,
      outcome: 'ok',
      replyLength: replyText.length,
    });

    let assistantMessageId: string | undefined;
    let status: ConversationOrchestrationStatus = 'completed';
    if (persistAssistant && replyText.length > 0) {
      try {
        const assistantDto: CreateMessageDto = {
          role: MessageRole.ASSISTANT,
          content: replyText,
        } as CreateMessageDto;
        const am = await this.messages.createForDialog(
          request.dialogId,
          assistantDto,
        );
        assistantMessageId = am.id;
        this.orchLog.logStructured('assistant_persist', {
          ...baseLog,
          assistantMessageId: am.id,
        });
      } catch (err) {
        status = 'completed_with_assistant_persist_warning';
        this.orchLog.warnStructured('assistant_persist', {
          ...baseLog,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }

    let deliveryReceipt: ConversationOrchestrationResult['deliveryReceipt'];
    let deliveryOutcome: ConversationDeliveryOutcome = { kind: 'skipped' };

    if (dispatch && replyText.length > 0) {
      const body = this.truncateForChannel(
        replyText,
        this.channel.capabilities.maxBodyLength,
      );
      const idempotencyKey = `${request.dialogId}:${userMessage.id}:assistant`;
      const correlation = request.correlationId
        ? { correlationId: request.correlationId }
        : undefined;
      if (deferDispatch) {
        try {
          const ack = await this.asyncJobs.dispatch({
            id: randomUUID(),
            type: 'channel.deliver',
            payload: {
              dialogId: request.dialogId,
              body,
              idempotencyKey,
              channelMetadata: request.channelMetadata,
            },
            correlation,
            idempotencyKey,
          });
          if (ack.accepted) {
            deliveryOutcome = { kind: 'async_enqueued', dispatch: ack };
            this.orchLog.logStructured('async_dispatch', {
              ...baseLog,
              outcome: 'accepted',
              jobId: ack.jobId,
            });
          } else {
            deliveryOutcome = {
              kind: 'async_enqueue_failed',
              error: ack.detail ?? 'dispatch_rejected',
            };
            status = 'completed_with_delivery_warning';
            this.orchLog.warnStructured('async_dispatch', {
              ...baseLog,
              outcome: 'rejected',
              detail: ack.detail,
            });
          }
        } catch (err) {
          deliveryOutcome = {
            kind: 'async_enqueue_failed',
            error: err instanceof Error ? err.message : String(err),
          };
          status = 'completed_with_delivery_warning';
          this.orchLog.warnStructured('async_dispatch', {
            ...baseLog,
            outcome: 'threw',
            error: err instanceof Error ? err.message : String(err),
          });
        }
      } else {
        try {
          const receipt = await this.channel.deliver({
            body,
            idempotencyKey,
            correlation,
            metadata: request.channelMetadata,
          });
          deliveryReceipt = receipt;
          if (receipt.status === 'failed') {
            deliveryOutcome = {
              kind: 'sync_failed',
              error: receipt.detail ?? 'delivery_failed',
            };
            status = 'completed_with_delivery_warning';
            this.orchLog.warnStructured('channel_dispatch', {
              ...baseLog,
              outcome: 'receipt_failed',
              detail: receipt.detail,
            });
          } else {
            deliveryOutcome = { kind: 'sync_delivered', receipt };
            this.orchLog.logStructured('channel_dispatch', {
              ...baseLog,
              outcome: 'ack',
            });
          }
        } catch (err) {
          deliveryOutcome = {
            kind: 'sync_failed',
            error: err instanceof Error ? err.message : String(err),
          };
          status = 'completed_with_delivery_warning';
          this.orchLog.warnStructured('channel_dispatch', {
            ...baseLog,
            outcome: 'threw',
            error: err instanceof Error ? err.message : String(err),
          });
        }
      }
    }

    timing.mark('delivery_complete');

    this.orchLog.logStructured('complete', {
      ...baseLog,
      status,
      userMessageId: userMessage.id,
      assistantMessageId,
    });

    const completed: ConversationOrchestrationResult = {
      status,
      dialogId: request.dialogId,
      correlationId: request.correlationId,
      userMessageId: userMessage.id,
      assistantMessageId,
      candidate,
      deliveryReceipt,
      deliveryOutcome,
      aiSalesDecision,
      toolProposals,
      toolExecution,
      operationsEnvelope,
      aiRefusal: traceRefusal,
      aiReplyMeta,
      assistantReplyQuality,
    };
    this.emitTurnTelemetry(
      timing,
      request,
      dialog,
      completed,
      'orchestration.turn_snapshot',
      request.executeTools === true,
    );
    return completed;
  }

  private emitTurnTelemetry(
    timing: OrchestrationTimingCollector,
    request: UserMessageOrchestrationRequest,
    dialog: Dialog | undefined,
    result: ConversationOrchestrationResult,
    eventKind:
      | 'orchestration.turn_snapshot'
      | 'orchestration.idempotency_hit',
    executeToolsRequested: boolean,
  ): void {
    timing.mark('turn_end');
    try {
      const timingModel = timing.build();
      const snapshot = buildOrchestrationTelemetrySnapshot({
        request,
        dialog: dialog
          ? {
              currentStage: String(dialog.currentStage),
              status: String(dialog.status),
              channel: String(dialog.channel),
            }
          : undefined,
        result,
        timing: timingModel,
        executeToolsRequested,
      });
      this.telemetryPublisher.publishStructured(
        buildOrchestrationTelemetryStructuredEvent(eventKind, snapshot),
      );
    } catch {
      /* defensive — publisher already isolates */
    }
  }

  private truncateForChannel(text: string, maxBodyLength: number): string {
    if (text.length <= maxBodyLength) {
      return text;
    }
    return text.slice(0, maxBodyLength);
  }
}
