import { Type } from 'class-transformer';
import {
  IsBoolean,
  IsObject,
  IsOptional,
  IsUUID,
  ValidateNested,
} from 'class-validator';
import type { OperationsEnvelopeV1 } from '../operations/contracts/operations-envelope.contract';

export class OperatorWorkspaceSignalsBodyDto {
  @IsOptional()
  @IsBoolean()
  takeoverActive?: boolean;
}

export class OperatorInboxRowRequestDto {
  @IsUUID()
  dialogId!: string;

  @IsOptional()
  @ValidateNested()
  @Type(() => OperatorWorkspaceSignalsBodyDto)
  workspaceSignals?: OperatorWorkspaceSignalsBodyDto;

  @IsOptional()
  @IsObject()
  lastOperationsEnvelope?: Readonly<Record<string, unknown>>;
}

export function toOperatorInboxQueryInput(
  dto: OperatorInboxRowRequestDto,
): {
  dialogId: string;
  workspaceSignals?: { takeoverActive?: boolean };
  lastOperationsEnvelope?: OperationsEnvelopeV1;
} {
  return {
    dialogId: dto.dialogId,
    workspaceSignals: dto.workspaceSignals
      ? { takeoverActive: dto.workspaceSignals.takeoverActive }
      : undefined,
    lastOperationsEnvelope: dto.lastOperationsEnvelope
      ? (dto.lastOperationsEnvelope as unknown as OperationsEnvelopeV1)
      : undefined,
  };
}
