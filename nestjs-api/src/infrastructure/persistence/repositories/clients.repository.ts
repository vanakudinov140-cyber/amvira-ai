import { Injectable } from '@nestjs/common';
import type { Client, Prisma } from '@prisma/client';
import { PrismaService } from '../prisma.service';
import { BasePrismaRepository } from './base.prisma-repository';

@Injectable()
export class ClientsRepository extends BasePrismaRepository {
  constructor(prisma: PrismaService) {
    super(prisma);
  }

  async create(data: Prisma.ClientCreateInput): Promise<Client> {
    return this.prisma.client.create({ data });
  }

  async findById(id: string): Promise<Client | null> {
    return this.prisma.client.findFirst({
      where: { id, deletedAt: null },
    });
  }

  async findManyPage(params: {
    skip: number;
    take: number;
  }): Promise<Client[]> {
    return this.prisma.client.findMany({
      where: { deletedAt: null },
      orderBy: { createdAt: 'desc' },
      skip: params.skip,
      take: params.take,
    });
  }

  async countActive(): Promise<number> {
    return this.prisma.client.count({ where: { deletedAt: null } });
  }
}
