import { Inject, Injectable, NotFoundException } from '@nestjs/common';
import type { Booking } from '@prisma/client';
import { BookingStatus } from '@prisma/client';
import { BookingsRepository } from '../../infrastructure/persistence/repositories/bookings.repository';
import {
  APPLICATION_EVENT_PUBLISHER,
  type ApplicationEventPublisher,
} from '../../shared/events/application-event.publisher';
import { ClientsService } from '../clients/clients.service';
import { CreateBookingDto } from './dto/create-booking.dto';
import { bookingCreatedEvent } from './events/booking-created.event';
import { bookingStatusChangedEvent } from './events/booking-status-changed.event';

@Injectable()
export class BookingsService {
  constructor(
    private readonly bookings: BookingsRepository,
    private readonly clients: ClientsService,
    @Inject(APPLICATION_EVENT_PUBLISHER)
    private readonly applicationEvents: ApplicationEventPublisher,
  ) {}

  async create(dto: CreateBookingDto): Promise<Booking> {
    await this.clients.assertExists(dto.clientId);
    const booking = await this.bookings.create({
      client: { connect: { id: dto.clientId } },
      service: dto.service,
      datetime: new Date(dto.datetime),
      status: BookingStatus.PENDING,
      notes: dto.notes,
    });

    this.applicationEvents.publish(
      bookingCreatedEvent({
        id: booking.id,
        clientId: booking.clientId,
        status: booking.status,
        datetime: booking.datetime,
      }),
    );

    return booking;
  }

  async applyYclientsSync(
    id: string,
    input: Readonly<{
      externalId?: string | null;
      syncStatus: string;
      syncError?: string | null;
    }>,
  ): Promise<Booking> {
    const updated = await this.bookings.updateYclientsSync(id, {
      yclientsExternalId: input.externalId ?? undefined,
      yclientsSyncStatus: input.syncStatus,
      yclientsSyncError: input.syncError ?? undefined,
    });
    if (!updated) {
      throw new NotFoundException(`Booking ${id} not found`);
    }
    return updated;
  }

  async findOne(id: string): Promise<Booking> {
    const booking = await this.bookings.findById(id);
    if (!booking) {
      throw new NotFoundException(`Booking ${id} not found`);
    }
    return booking;
  }

  async updateStatus(id: string, status: BookingStatus): Promise<Booking> {
    const previous = await this.findOne(id);
    const updated = await this.bookings.updateStatus(id, status);
    if (!updated) {
      throw new NotFoundException(`Booking ${id} not found`);
    }

    if (previous.status !== updated.status) {
      this.applicationEvents.publish(
        bookingStatusChangedEvent({
          bookingId: updated.id,
          clientId: updated.clientId,
          previousStatus: previous.status,
          newStatus: updated.status,
        }),
      );
    }

    return updated;
  }
}
