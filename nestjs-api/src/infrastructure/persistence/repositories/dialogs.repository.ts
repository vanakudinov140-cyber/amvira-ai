import { Injectable } from '@nestjs/common';
import type { Dialog, DialogStage, Prisma } from '@prisma/client';
import { PrismaService } from '../prisma.service';
import { BasePrismaRepository } from './base.prisma-repository';

@Injectable()
export class DialogsRepository extends BasePrismaRepository {
  constructor(prisma: PrismaService) {
    super(prisma);
  }

  async createWithInitialState(
    data: Prisma.DialogCreateInput,
  ): Promise<Dialog> {
    return this.prisma.$transaction(async (tx) => {
      const dialog = await tx.dialog.create({ data });
      await tx.dialogState.create({
        data: {
          dialogId: dialog.id,
          stage: dialog.currentStage,
        },
      });
      return dialog;
    });
  }

  async findById(id: string): Promise<Dialog | null> {
    return this.prisma.dialog.findFirst({
      where: { id, deletedAt: null },
    });
  }

  async appendStateAndSetStage(
    dialogId: string,
    newStage: DialogStage,
    payload?: Prisma.InputJsonValue,
  ): Promise<Dialog> {
    return this.prisma.$transaction(async (tx) => {
      await tx.dialogState.create({
        data: { dialogId, stage: newStage, payload },
      });
      const updated = await tx.dialog.updateMany({
        where: { id: dialogId, deletedAt: null },
        data: { currentStage: newStage },
      });
      if (updated.count === 0) {
        throw new Error(`Dialog ${dialogId} not found or deleted`);
      }
      return tx.dialog.findFirstOrThrow({
        where: { id: dialogId, deletedAt: null },
      });
    });
  }
}
