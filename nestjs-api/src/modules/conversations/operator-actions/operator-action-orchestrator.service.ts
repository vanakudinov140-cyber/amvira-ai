import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { DialogStage, MessageRole } from '@prisma/client';
import { DialogsService } from '../../dialogs/dialogs.service';
import { CreateMessageDto } from '../../messages/dto/create-message.dto';
import { MessagesService } from '../../messages/messages.service';
import {
  buildOperatorAuditSnapshot,
  singleAuditLine,
} from '../operator-audit/operator-audit.builder';
import { assertOperatorCommandAuthorized } from '../operator-policies/operator-permission.policy';
import { validateOperatorCommandExecution } from '../operator-policies/operator-command-validation.policy';
import type { OperatorCommandEnvelopeV1 } from '../operator-contracts/operator-command.contract';
import type { OperatorActionOrchestrationResultV1 } from './operator-action-result.contract';

/**
 * Human-in-the-loop command execution — not AI orchestration; uses application services only.
 */
@Injectable()
export class OperatorActionOrchestratorService {
  constructor(
    private readonly dialogs: DialogsService,
    private readonly messages: MessagesService,
  ) {}

  async execute(
    envelope: OperatorCommandEnvelopeV1,
  ): Promise<OperatorActionOrchestrationResultV1> {
    const authz = assertOperatorCommandAuthorized(
      envelope.command.kind,
      envelope.authorization,
    );
    if (!authz.ok) {
      return {
        resultVersion: 'operator_action_orchestration@v1',
        status: 'rejected',
        rejection: { code: authz.code, detail: authz.detail },
        audit: buildOperatorAuditSnapshot({
          envelope,
          outcomeStatus: 'rejected',
          lines: [singleAuditLine('authorization', authz.detail)],
        }),
      };
    }

    let dialog;
    try {
      dialog = await this.dialogs.findOne(envelope.dialogId);
    } catch (e) {
      if (e instanceof NotFoundException) {
        return {
          resultVersion: 'operator_action_orchestration@v1',
          status: 'failed',
          rejection: { code: 'dialog_not_found', detail: envelope.dialogId },
          audit: buildOperatorAuditSnapshot({
            envelope,
            outcomeStatus: 'failed',
            lines: [singleAuditLine('dialog', 'not_found')],
          }),
        };
      }
      throw e;
    }

    const dialogSnapshot = {
      currentStage: String(dialog.currentStage),
      status: String(dialog.status),
    };

    const validated = validateOperatorCommandExecution({
      envelope,
      dialog: dialogSnapshot,
    });

    if (!validated.ok) {
      return {
        resultVersion: 'operator_action_orchestration@v1',
        status: 'rejected',
        rejection: { code: validated.code, detail: validated.detail },
        audit: buildOperatorAuditSnapshot({
          envelope,
          outcomeStatus: 'rejected',
          lines: [
            singleAuditLine(
              'validation',
              `${validated.code}:${validated.detail ?? ''}`,
            ),
          ],
        }),
      };
    }

    const lines: ReturnType<typeof singleAuditLine>[] = [];

    try {
      switch (envelope.command.kind) {
        case 'operator.reply': {
          const body = validated.parsedReply!.body;
          const dto: CreateMessageDto = {
            role: MessageRole.SYSTEM,
            content: body,
            metadata: {
              origin: 'operator_command',
              commandKind: envelope.command.kind,
              correlationId: envelope.correlationId ?? null,
              operatorLabel: validated.parsedReply!.operatorLabel ?? null,
              operatorId: envelope.actor?.operatorId ?? null,
            },
          } as CreateMessageDto;
          const msg = await this.messages.createForDialog(envelope.dialogId, dto);
          lines.push(
            singleAuditLine('message_created', `messageId=${msg.id};role=SYSTEM`),
          );
          break;
        }
        case 'dialog.stage.transition': {
          const target = validated.parsedStage!.targetStage as DialogStage;
          await this.dialogs.transitionStage(envelope.dialogId, {
            stage: target,
            payload: validated.parsedStage!.workflowPayload,
          });
          lines.push(
            singleAuditLine(
              'stage_transitioned',
              `to=${validated.parsedStage!.targetStage}`,
            ),
          );
          break;
        }
        case 'escalation.resolve': {
          const { resolutionCode, note } = validated.parsedEscalation!;
          const summary = `[escalation.resolved] code=${resolutionCode}${note ? ` note=${note}` : ''}`;
          const dto: CreateMessageDto = {
            role: MessageRole.SYSTEM,
            content: summary,
            metadata: {
              origin: 'operator_command',
              commandKind: envelope.command.kind,
              resolutionCode,
              note: note ?? null,
              correlationId: envelope.correlationId ?? null,
            },
          } as CreateMessageDto;
          const msg = await this.messages.createForDialog(envelope.dialogId, dto);
          lines.push(
            singleAuditLine('escalation_resolved', `messageId=${msg.id}`),
          );
          break;
        }
        case 'takeover.activate': {
          lines.push(singleAuditLine('takeover', 'activate_signal'));
          const dto: CreateMessageDto = {
            role: MessageRole.SYSTEM,
            content:
              '[takeover.active] operator assumed control (transient signal).',
            metadata: {
              origin: 'operator_command',
              commandKind: envelope.command.kind,
              correlationId: envelope.correlationId ?? null,
            },
          } as CreateMessageDto;
          await this.messages.createForDialog(envelope.dialogId, dto);
          return {
            resultVersion: 'operator_action_orchestration@v1',
            status: 'completed',
            transientTakeover: {
              stateVersion: 'operator_takeover_state@v1',
              active: true,
              source: 'command_execution',
            },
            transientSuppression: {
              suppressionVersion: 'operator_assistant_suppression@v1',
              suggestHoldAssistantOutbound: true,
            },
            audit: buildOperatorAuditSnapshot({
              envelope,
              outcomeStatus: 'completed',
              lines: [...lines, singleAuditLine('message', 'takeover_marker')],
            }),
          };
        }
        case 'takeover.deactivate': {
          lines.push(singleAuditLine('takeover', 'release_signal'));
          const dto: CreateMessageDto = {
            role: MessageRole.SYSTEM,
            content:
              '[takeover.released] operator released control (transient signal).',
            metadata: {
              origin: 'operator_command',
              commandKind: envelope.command.kind,
              correlationId: envelope.correlationId ?? null,
            },
          } as CreateMessageDto;
          await this.messages.createForDialog(envelope.dialogId, dto);
          return {
            resultVersion: 'operator_action_orchestration@v1',
            status: 'completed',
            transientTakeover: {
              stateVersion: 'operator_takeover_state@v1',
              active: false,
              source: 'command_execution',
            },
            transientSuppression: {
              suppressionVersion: 'operator_assistant_suppression@v1',
              suggestHoldAssistantOutbound: false,
            },
            audit: buildOperatorAuditSnapshot({
              envelope,
              outcomeStatus: 'completed',
              lines: [
                ...lines,
                singleAuditLine('message', 'takeover_release_marker'),
              ],
            }),
          };
        }
        case 'assistant.resume_signal': {
          lines.push(singleAuditLine('assistant', 'resume_signal'));
          return {
            resultVersion: 'operator_action_orchestration@v1',
            status: 'completed',
            resumeAssistantSuggested: true,
            transientSuppression: {
              suppressionVersion: 'operator_assistant_suppression@v1',
              suggestHoldAssistantOutbound: false,
            },
            audit: buildOperatorAuditSnapshot({
              envelope,
              outcomeStatus: 'completed',
              lines,
            }),
          };
        }
        case 'assistant.override_ack': {
          const note =
            typeof envelope.command.payload.note === 'string'
              ? envelope.command.payload.note
              : undefined;
          const dto: CreateMessageDto = {
            role: MessageRole.SYSTEM,
            content: `[assistant.override.ack] ${note ?? 'acknowledged'}`,
            metadata: {
              origin: 'operator_command',
              commandKind: envelope.command.kind,
              correlationId: envelope.correlationId ?? null,
            },
          } as CreateMessageDto;
          const msg = await this.messages.createForDialog(envelope.dialogId, dto);
          lines.push(singleAuditLine('override_ack', `messageId=${msg.id}`));
          break;
        }
      }

      return {
        resultVersion: 'operator_action_orchestration@v1',
        status: 'completed',
        audit: buildOperatorAuditSnapshot({
          envelope,
          outcomeStatus: 'completed',
          lines,
        }),
      };
    } catch (e) {
      const detail =
        e instanceof BadRequestException
          ? e.message
          : e instanceof Error
            ? e.message
            : String(e);
      return {
        resultVersion: 'operator_action_orchestration@v1',
        status: 'failed',
        rejection: { code: 'execution_error', detail },
        audit: buildOperatorAuditSnapshot({
          envelope,
          outcomeStatus: 'failed',
          lines: [...lines, singleAuditLine('execution_error', detail)],
        }),
      };
    }
  }
}
