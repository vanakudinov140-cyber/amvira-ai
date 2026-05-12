import { Injectable } from '@nestjs/common';
import { DialogChannel } from '@prisma/client';
import { IntegrationLoggingService } from '../../common/logging/integration-logging.service';
import { AiTone } from './ai-tone.enum';
import { PersonalizeCommunicationDto } from './dto/personalize-communication.dto';

const tonePrefixes: Record<AiTone, string> = {
  [AiTone.Neutral]: '',
  [AiTone.Friendly]: '[Friendly] ',
};

@Injectable()
export class AiCommunicationIntegration {
  private static readonly integrationKey = 'AiCommunication';

  constructor(private readonly integrationLog: IntegrationLoggingService) {}

  /**
   * AI boundary: tone and phrasing only. No workflow, CRM, validation, or booking.
   */
  async personalizeTone(input: PersonalizeCommunicationDto): Promise<string> {
    await Promise.resolve();
    const operation = 'personalizeTone';
    this.integrationLog.logIntegrationRequest(
      AiCommunicationIntegration.integrationKey,
      operation,
      {
        channel: DialogChannel.API,
        tone: input.tone,
        length: input.text.length,
      },
    );
    this.integrationLog.logAiRequest({
      tone: input.tone,
      length: input.text.length,
    });

    const prefix = tonePrefixes[input.tone] ?? '';
    const output = `${prefix}${input.text}`;

    this.integrationLog.logAiResponse({
      tone: input.tone,
      outputLength: output.length,
    });
    this.integrationLog.logIntegrationResponse(
      AiCommunicationIntegration.integrationKey,
      operation,
      {
        channel: DialogChannel.API,
        outputLength: output.length,
      },
    );

    return output;
  }
}
