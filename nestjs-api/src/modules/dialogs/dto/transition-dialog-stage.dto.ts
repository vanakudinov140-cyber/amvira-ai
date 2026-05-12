import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { DialogStage } from '@prisma/client';
import { IsEnum, IsObject, IsOptional } from 'class-validator';

export class TransitionDialogStageDto {
  @ApiProperty({
    description: 'Target workflow stage (validated in service, not by AI)',
    enum: DialogStage,
  })
  @IsEnum(DialogStage)
  stage!: DialogStage;

  @ApiPropertyOptional({
    description: 'Opaque workflow context (CRM ids, slot hints, etc.)',
  })
  @IsOptional()
  @IsObject()
  payload?: Record<string, unknown>;
}
