import { Type } from 'class-transformer';
import {
  ArrayMaxSize,
  ArrayMinSize,
  IsArray,
  IsObject,
  IsOptional,
  IsUUID,
} from 'class-validator';
import { OperatorOffsetPageQueryDto } from './operator-pagination.dto';

export class OperatorInboxPreviewRequestDto extends OperatorOffsetPageQueryDto {
  @IsArray()
  @ArrayMinSize(1)
  @ArrayMaxSize(200)
  @IsUUID('4', { each: true })
  dialogIds!: string[];

  @IsOptional()
  @IsObject()
  contextByDialogId?: Readonly<
    Record<string, Readonly<Record<string, unknown>>>
  >;
}
