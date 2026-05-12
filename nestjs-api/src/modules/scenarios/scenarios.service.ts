import { Injectable } from '@nestjs/common';
import type { Scenario } from '@prisma/client';
import { ScenariosRepository } from '../../infrastructure/persistence/repositories/scenarios.repository';

@Injectable()
export class ScenariosService {
  constructor(private readonly scenarios: ScenariosRepository) {}

  async findActive(): Promise<Scenario[]> {
    return this.scenarios.findActive();
  }
}
