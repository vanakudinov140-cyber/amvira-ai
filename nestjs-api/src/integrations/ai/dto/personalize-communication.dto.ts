import { ApiProperty } from '@nestjs/swagger';
import { IsEnum, IsString, MaxLength, MinLength } from 'class-validator';
import { AiTone } from '../ai-tone.enum';

export class PersonalizeCommunicationDto {
  @ApiProperty({ minLength: 1, maxLength: 8000 })
  @IsString()
  @MinLength(1)
  @MaxLength(8000)
  text!: string;

  @ApiProperty({ enum: AiTone })
  @IsEnum(AiTone)
  tone!: AiTone;
}
