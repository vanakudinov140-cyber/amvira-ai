import { Type } from 'class-transformer';
import { IsInt, IsOptional, Max, Min } from 'class-validator';

export class OperatorTimelineQueryDto {
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(10)
  @Max(2000)
  eventLimit = 500;
}
