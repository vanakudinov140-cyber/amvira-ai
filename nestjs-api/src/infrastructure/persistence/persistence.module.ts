import { Global, Module } from '@nestjs/common';
import { PrismaModule } from './prisma.module';
import { BookingsRepository } from './repositories/bookings.repository';
import { ClientsRepository } from './repositories/clients.repository';
import { DialogsRepository } from './repositories/dialogs.repository';
import { MessagesRepository } from './repositories/messages.repository';
import { ScenariosRepository } from './repositories/scenarios.repository';

@Global()
@Module({
  imports: [PrismaModule],
  providers: [
    ClientsRepository,
    DialogsRepository,
    MessagesRepository,
    BookingsRepository,
    ScenariosRepository,
  ],
  exports: [
    PrismaModule,
    ClientsRepository,
    DialogsRepository,
    MessagesRepository,
    BookingsRepository,
    ScenariosRepository,
  ],
})
export class PersistenceModule {}
