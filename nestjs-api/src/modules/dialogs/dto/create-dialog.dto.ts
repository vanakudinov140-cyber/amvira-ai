import { ApiProperty } from '@nestjs/swagger';
import { DialogChannel, ScenarioCode } from '@prisma/client';
import { IsEnum, IsUUID } from 'class-validator';

export class CreateDialogDto {
  @ApiProperty({ format: 'uuid' })
  @IsUUID('4')
  clientId!: string;

  @ApiProperty({ enum: DialogChannel })
  @IsEnum(DialogChannel)
  channel!: DialogChannel;

  @ApiProperty({ enum: ScenarioCode })
  @IsEnum(ScenarioCode)
  scenarioCode!: ScenarioCode;
}
