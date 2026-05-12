import { BullModule } from '@nestjs/bullmq';
import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { IntegrationLoggingModule } from '../../common/logging/integration-logging.module';
import configuration from '../../config/configuration';
import { validationSchema } from '../../config/env.validation';
import {
  AiIntegrationModule,
  FlowsellModule,
  GigachatModule,
  TelegramModule,
  WhatsappModule,
  YclientsModule,
} from '../../integrations';
import { AppLoggerModule } from '../../infrastructure/logger/app-logger.module';
import { PersistenceModule } from '../../infrastructure/persistence/persistence.module';
import { SchedulersModule } from '../../infrastructure/schedulers/schedulers.module';
import { ApplicationEventsModule } from '../../shared/events/application-events.module';
import { AiModule } from '../ai/ai.module';
import { BookingsModule } from '../bookings/bookings.module';
import { ChannelsModule } from '../channels/channels.module';
import { ClientsModule } from '../clients/clients.module';
import { ConversationsModule } from '../conversations/conversations.module';
import { DialogsModule } from '../dialogs/dialogs.module';
import { HealthModule } from '../health/health.module';
import { IntegrationsBoundaryModule } from '../integrations/integrations-boundary.module';
import { MessagesModule } from '../messages/messages.module';
import { QueueModule } from '../queue/queue.module';
import { ScenariosModule } from '../scenarios/scenarios.module';
import { AppController } from './app.controller';
import { AppService } from './app.service';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      validationSchema,
      validationOptions: {
        abortEarly: true,
        allowUnknown: true,
      },
    }),
    BullModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        connection: {
          host: config.get<string>('redis.host'),
          port: config.get<number>('redis.port'),
          password: config.get<string>('redis.password') || undefined,
        },
      }),
      inject: [ConfigService],
    }),
    AppLoggerModule,
    IntegrationLoggingModule,
    PersistenceModule,
    ApplicationEventsModule,
    AiModule,
    IntegrationsBoundaryModule,
    ChannelsModule,
    ConversationsModule,
    AiIntegrationModule,
    GigachatModule,
    YclientsModule,
    FlowsellModule,
    TelegramModule,
    WhatsappModule,
    ClientsModule,
    ScenariosModule,
    DialogsModule,
    MessagesModule,
    BookingsModule,
    HealthModule,
    QueueModule,
    SchedulersModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
