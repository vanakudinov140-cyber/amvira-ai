import { Module } from '@nestjs/common';
import { ClientsModule } from '../clients/clients.module';
import { DialogsController } from './dialogs.controller';
import { DialogsService } from './dialogs.service';

@Module({
  imports: [ClientsModule],
  controllers: [DialogsController],
  providers: [DialogsService],
  exports: [DialogsService],
})
export class DialogsModule {}
