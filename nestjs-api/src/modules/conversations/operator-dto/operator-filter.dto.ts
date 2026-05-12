import { IsOptional, IsString, MaxLength } from 'class-validator';

/**
 * Reserved API filters — not applied server-side until inbox search exists.
 */
export class OperatorInboxFilterQueryDto {
  @IsOptional()
  @IsString()
  @MaxLength(64)
  stageHint?: string;
}
