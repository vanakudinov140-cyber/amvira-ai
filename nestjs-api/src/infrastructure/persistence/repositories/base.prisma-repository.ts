import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma.service';

@Injectable()
export abstract class BasePrismaRepository {
  protected constructor(protected readonly prisma: PrismaService) {}
}
