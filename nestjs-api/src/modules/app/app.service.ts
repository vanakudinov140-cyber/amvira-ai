import { Injectable, Logger } from '@nestjs/common';
import { ClientsRepository } from '../../infrastructure/persistence/repositories/clients.repository';
import { HelloResponseDto } from './dto/hello-response.dto';

@Injectable()
export class AppService {
  private readonly logger = new Logger(AppService.name);

  constructor(private readonly clients: ClientsRepository) {}

  async getHello(): Promise<HelloResponseDto> {
    const activeClients = await this.clients.countActive();
    this.logger.log(
      JSON.stringify({ msg: 'app.summary', activeClients }),
      AppService.name,
    );
    return { message: 'Hello World!' };
  }
}
