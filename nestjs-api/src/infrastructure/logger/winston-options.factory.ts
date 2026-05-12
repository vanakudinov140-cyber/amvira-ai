import type { ConfigService } from '@nestjs/config';
import {
  utilities as nestWinstonModuleUtilities,
  WinstonModuleOptions,
} from 'nest-winston';
import * as winston from 'winston';

export function buildWinstonOptions(
  config: ConfigService,
): WinstonModuleOptions {
  const isProd = config.get<string>('app.nodeEnv') === 'production';

  if (isProd) {
    return {
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.json(),
          ),
        }),
      ],
    };
  }

  return {
    transports: [
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.ms(),
          nestWinstonModuleUtilities.format.nestLike('Nest', {
            colors: true,
            prettyPrint: true,
          }),
        ),
      }),
    ],
  };
}
