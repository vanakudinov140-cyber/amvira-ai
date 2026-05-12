import { Injectable } from '@nestjs/common';
import type { Booking, BookingStatus, Prisma } from '@prisma/client';
import { PrismaService } from '../prisma.service';
import { BasePrismaRepository } from './base.prisma-repository';

@Injectable()
export class BookingsRepository extends BasePrismaRepository {
  constructor(prisma: PrismaService) {
    super(prisma);
  }

  async create(data: Prisma.BookingCreateInput): Promise<Booking> {
    return this.prisma.booking.create({ data });
  }

  async findById(id: string): Promise<Booking | null> {
    return this.prisma.booking.findFirst({
      where: { id, deletedAt: null },
    });
  }

  async updateStatus(
    id: string,
    status: BookingStatus,
  ): Promise<Booking | null> {
    const result = await this.prisma.booking.updateMany({
      where: { id, deletedAt: null },
      data: { status },
    });
    if (result.count === 0) {
      return null;
    }
    return this.findById(id);
  }

  async updateYclientsSync(
    id: string,
    data: Prisma.BookingUpdateInput,
  ): Promise<Booking | null> {
    try {
      return await this.prisma.booking.update({
        where: { id, deletedAt: null },
        data,
      });
    } catch {
      return null;
    }
  }
}
