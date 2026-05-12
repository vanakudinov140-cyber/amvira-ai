import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { MessageRole } from '@prisma/client';
import {
  IsEnum,
  IsObject,
  IsOptional,
  IsString,
  MaxLength,
  MinLength,
} from 'class-validator';

export class CreateMessageDto {
  @ApiProperty({ enum: MessageRole })
  @IsEnum(MessageRole)
  role!: MessageRole;

  @ApiProperty()
  @IsString()
  @MinLength(1)
  @MaxLength(32000)
  content!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsObject()
  metadata?: Record<string, unknown>;
}
