import { Test, TestingModule } from '@nestjs/testing';
import { ClientsRepository } from '../../infrastructure/persistence/repositories/clients.repository';
import { AppController } from './app.controller';
import { AppService } from './app.service';

describe('AppController', () => {
  let appController: AppController;

  beforeEach(async () => {
    const app: TestingModule = await Test.createTestingModule({
      controllers: [AppController],
      providers: [
        AppService,
        {
          provide: ClientsRepository,
          useValue: {
            countActive: jest.fn((): Promise<number> => Promise.resolve(0)),
          },
        },
      ],
    }).compile();

    appController = app.get<AppController>(AppController);
  });

  it('should return hello dto', async () => {
    await expect(appController.getHello()).resolves.toEqual({
      message: 'Hello World!',
    });
  });
});
