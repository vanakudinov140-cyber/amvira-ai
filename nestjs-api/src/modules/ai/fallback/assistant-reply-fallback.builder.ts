import { Injectable } from '@nestjs/common';
import type { DialogStageCode } from '../../dialogs/domain/dialog-stage.types';
import { isDialogStageCode } from '../../dialogs/domain/dialog-stage.types';

export type AssistantFallbackContext = Readonly<{
  readonly currentStage: string;
  readonly channel: string;
  readonly userText: string;
  readonly reason: 'timeout' | 'refusal' | 'failure' | 'validation';
}>;

@Injectable()
export class AssistantReplyFallbackBuilder {
  build(ctx: AssistantFallbackContext): { readonly replyText: string } {
    const stage = isDialogStageCode(ctx.currentStage)
      ? (ctx.currentStage as DialogStageCode)
      : 'DISCOVERY';
    const short =
      ctx.channel === 'TELEGRAM'
        ? true
        : ctx.userText.length < 400;
    const prefix =
      ctx.reason === 'timeout'
        ? 'Сейчас не удалось быстро сгенерировать ответ.'
        : 'Не могу сейчас выдать полноценный ответ автоматически.';
    const bodyByStage: Record<DialogStageCode, string> = {
      TRUST_BUILDING:
        'Я на связи. Коротко: чем помочь в первую очередь — подбор услуги, вопрос по записи или консультация?',
      DISCOVERY:
        'Расскажите в одном сообщении, что хотите получить после визита — подберу варианты без лишних обещаний.',
      PRESENTATION:
        'Могу кратко описать подходящие варианты. Что важнее: результат, время или бюджет?',
      OBJECTION_HANDLING:
        'Понимаю сомнения. Если удобно — уточните, что именно смущает, и я отвечу по существу одним следующим сообщением.',
      BOOKING:
        'Чтобы записаться без ошибок, напишите желаемую услугу и примерные дни/время — я уточню детали.',
      COMPLETED:
        'Спасибо за диалог. Если нужно продолжить — напишите, что именно осталось открытым.',
    };
    const tail = short
      ? ' Если нужен администратор — напишите «оператор».'
      : ' Если вопрос срочный или требует ручной проверки слотов, напишите «оператор» — передадим коллегам.';
    return {
      replyText: `${prefix} ${bodyByStage[stage]}${tail}`,
    };
  }
}
