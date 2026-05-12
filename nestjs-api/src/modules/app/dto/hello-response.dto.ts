import { ApiProperty } from '@nestjs/swagger';
import { IsString } from 'class-validator';

export class HelloResponseDto {
  @ApiProperty({ example: 'Hello World!' })
  @IsString()
  message!: string;
}
