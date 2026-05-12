import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import {
  IsDateString,
  IsOptional,
  IsString,
  IsUUID,
  MaxLength,
  MinLength,
} from 'class-validator';

export class CreateBookingDto {
  @ApiProperty({ format: 'uuid' })
  @IsUUID('4')
  clientId!: string;

  @ApiProperty({ example: 'Balayage' })
  @IsString()
  @MinLength(1)
  @MaxLength(500)
  service!: string;

  @ApiProperty({ example: '2026-05-20T14:00:00.000Z' })
  @IsDateString()
  datetime!: string;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  @MaxLength(2000)
  notes?: string;
}
