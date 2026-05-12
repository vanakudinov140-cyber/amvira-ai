import {
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
} from '@nestjs/common';
import { ApiCreatedResponse, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import type { Booking } from '@prisma/client';
import { BookingsService } from './bookings.service';
import { CreateBookingDto } from './dto/create-booking.dto';
import { UpdateBookingStatusDto } from './dto/update-booking-status.dto';

@ApiTags('bookings')
@Controller('bookings')
export class BookingsController {
  constructor(private readonly bookingsService: BookingsService) {}

  @Post()
  @ApiCreatedResponse({
    description: 'Booking created (business status PENDING)',
  })
  async create(@Body() dto: CreateBookingDto): Promise<Booking> {
    return await this.bookingsService.create(dto);
  }

  @Get(':id')
  @ApiOkResponse({ description: 'Booking by id' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Booking> {
    return await this.bookingsService.findOne(id);
  }

  @Patch(':id/status')
  @ApiOkResponse({ description: 'Booking status updated' })
  async updateStatus(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateBookingStatusDto,
  ): Promise<Booking> {
    return await this.bookingsService.updateStatus(id, dto.status);
  }
}
