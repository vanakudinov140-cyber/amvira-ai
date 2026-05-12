import { Injectable } from '@nestjs/common';
import type { Scenario, ScenarioCode } from '@prisma/client';
import { PrismaService } from '../prisma.service';
import { BasePrismaRepository } from './base.prisma-repository';

@Injectable()
export class ScenariosRepository extends BasePrismaRepository {
  constructor(prisma: PrismaService) {
    super(prisma);
  }

  async findActive(): Promise<Scenario[]> {
    return this.prisma.scenario.findMany({
      where: { deletedAt: null, isActive: true },
      orderBy: { name: 'asc' },
    });
  }

  async findByCode(code: ScenarioCode): Promise<Scenario | null> {
    return this.prisma.scenario.findFirst({
      where: { code, deletedAt: null },
    });
  }
}
