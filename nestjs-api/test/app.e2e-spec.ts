import { INestApplication } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { App } from 'supertest/types';
import { AppModule } from '../src/modules/app/app.module';

describe('App (e2e)', () => {
  let app: INestApplication<App>;

  beforeEach(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  it('/ (GET)', async () => {
    const res = await request(app.getHttpServer()).get('/').expect(200);
    expect(res.body).toEqual({ message: 'Hello World!' });
  });

  it('/health (GET)', async () => {
    await request(app.getHttpServer()).get('/health').expect(200);
  });
});
