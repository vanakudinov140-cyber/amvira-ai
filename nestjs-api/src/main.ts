import { Logger, RequestMethod, ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { json, urlencoded, type NextFunction, type Request, type Response } from 'express';
import { WINSTON_MODULE_NEST_PROVIDER } from 'nest-winston';
import { AppModule } from './modules/app/app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    bufferLogs: true,
    bodyParser: false,
  });
  app.enableShutdownHooks();

  const config = app.get(ConfigService);
  const expressApp = app.getHttpAdapter().getInstance() as import('express').Application;

  if (config.get<boolean>('server.trustProxy')) {
    expressApp.set('trust proxy', 1);
  }

  const bodyLimit = config.get<string>('server.requestBodyLimit') ?? '512kb';
  expressApp.use(json({ limit: bodyLimit }));
  expressApp.use(urlencoded({ extended: false, limit: bodyLimit }));

  const httpLogger = new Logger('HTTP');
  expressApp.use((req: Request, res: Response, next: NextFunction) => {
    const start = Date.now();
    res.on('finish', () => {
      const path = req.originalUrl ?? req.url;
      httpLogger.log(
        `${req.method} ${path} ${res.statusCode} +${Date.now() - start}ms`,
      );
    });
    next();
  });

  app.useLogger(app.get(WINSTON_MODULE_NEST_PROVIDER));

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidUnknownValues: true,
    }),
  );

  app.setGlobalPrefix('api', {
    exclude: [
      { path: 'health/live', method: RequestMethod.GET },
      { path: 'health/ready', method: RequestMethod.GET },
      { path: 'health', method: RequestMethod.GET },
      { path: 'docs', method: RequestMethod.GET },
    ],
  });

  const swaggerConfig = new DocumentBuilder()
    .setTitle('Beauty salon assistant API')
    .setDescription(
      'Beauty salon assistant platform API — clients, dialogs, bookings, scenarios; AI handles wording only.',
    )
    .setVersion('1.0')
    .build();
  const document = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('docs', app, document);

  const port = config.get<number>('app.port') ?? 3000;
  await app.listen(port);
}
void bootstrap();
