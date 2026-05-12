import { Global, Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { WinstonModule } from 'nest-winston';
import { buildWinstonOptions } from './winston-options.factory';

@Global()
@Module({
  imports: [
    WinstonModule.forRootAsync({
      imports: [ConfigModule],
      inject: [ConfigService],
      useFactory: (config: ConfigService) => buildWinstonOptions(config),
    }),
  ],
  exports: [WinstonModule],
})
export class AppLoggerModule {}
