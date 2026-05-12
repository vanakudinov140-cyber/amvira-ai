import {
  IsIn,
  IsObject,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
} from 'class-validator';
import { OPERATOR_COMMAND_KINDS } from '../operator-contracts/operator-command.contract';
import type { OperatorCommandEnvelopeV1 } from '../operator-contracts/operator-command.contract';
import type { OperatorCommandKindV1 } from '../operator-contracts/operator-command.contract';
import type { OperatorAuthorizationContextV1 } from '../operator-contracts/operator-permissions.contract';

const COMMAND_KIND_LIST = [...OPERATOR_COMMAND_KINDS] as string[];

export class ExecuteOperatorActionDto {
  @IsUUID()
  dialogId!: string;

  @IsOptional()
  @IsString()
  @MaxLength(128)
  correlationId?: string;

  @IsIn(COMMAND_KIND_LIST)
  commandKind!: OperatorCommandKindV1;

  @IsOptional()
  @IsObject()
  payload?: Readonly<Record<string, unknown>>;

  @IsOptional()
  @IsObject()
  authorization?: Readonly<Record<string, unknown>>;

  @IsOptional()
  @IsObject()
  actor?: Readonly<Record<string, unknown>>;
}

export function toOperatorCommandEnvelope(
  dto: ExecuteOperatorActionDto,
): OperatorCommandEnvelopeV1 {
  return {
    envelopeVersion: 'operator_command_envelope@v1',
    dialogId: dto.dialogId,
    correlationId: dto.correlationId,
    command: {
      commandVersion: 'operator_command@v1',
      kind: dto.commandKind,
      payload: dto.payload ?? {},
    },
    authorization: dto.authorization as
      | OperatorAuthorizationContextV1
      | undefined,
    actor: dto.actor as
      | Readonly<{ operatorId?: string; label?: string }>
      | undefined,
  };
}
