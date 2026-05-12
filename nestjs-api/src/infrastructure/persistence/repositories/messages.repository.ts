import { Injectable } from '@nestjs/common';
import type { Message, Prisma } from '@prisma/client';
import { PrismaService } from '../prisma.service';
import { BasePrismaRepository } from './base.prisma-repository';

@Injectable()
export class MessagesRepository extends BasePrismaRepository {
  constructor(prisma: PrismaService) {
    super(prisma);
  }

  async create(data: Prisma.MessageCreateInput): Promise<Message> {
    return this.prisma.message.create({ data });
  }

  async findByDialogId(dialogId: string): Promise<Message[]> {
    return this.prisma.message.findMany({
      where: { dialogId, deletedAt: null },
      orderBy: { createdAt: 'asc' },
    });
  }
}
