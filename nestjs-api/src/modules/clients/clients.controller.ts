import {
  Body,
  Controller,
  Get,
  Param,
  ParseUUIDPipe,
  Post,
  Query,
} from '@nestjs/common';
import { ApiCreatedResponse, ApiOkResponse, ApiTags } from '@nestjs/swagger';
import type { Client } from '@prisma/client';
import { PaginationQueryDto } from '../../common/dto/pagination-query.dto';
import { ClientsService } from './clients.service';
import { CreateClientDto } from './dto/create-client.dto';

@ApiTags('clients')
@Controller('clients')
export class ClientsController {
  constructor(private readonly clientsService: ClientsService) {}

  @Post()
  @ApiCreatedResponse({ description: 'Client created' })
  async create(@Body() dto: CreateClientDto): Promise<Client> {
    return await this.clientsService.create(dto);
  }

  @Get()
  @ApiOkResponse({ description: 'Paged clients' })
  async findPage(@Query() query: PaginationQueryDto): Promise<Client[]> {
    return await this.clientsService.findPage(query);
  }

  @Get(':id')
  @ApiOkResponse({ description: 'Client by id' })
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<Client> {
    return await this.clientsService.findOne(id);
  }
}
