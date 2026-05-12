import { Injectable, NotFoundException } from '@nestjs/common';
import type { Client } from '@prisma/client';
import { PaginationQueryDto } from '../../common/dto/pagination-query.dto';
import { ClientsRepository } from '../../infrastructure/persistence/repositories/clients.repository';
import { CreateClientDto } from './dto/create-client.dto';

@Injectable()
export class ClientsService {
  constructor(private readonly clients: ClientsRepository) {}

  async create(dto: CreateClientDto): Promise<Client> {
    return this.clients.create({
      name: dto.name,
      phone: dto.phone,
      telegram: dto.telegram,
      whatsapp: dto.whatsapp,
      clientType: dto.clientType,
      notes: dto.notes,
    });
  }

  async findOne(id: string): Promise<Client> {
    const client = await this.clients.findById(id);
    if (!client) {
      throw new NotFoundException(`Client ${id} not found`);
    }
    return client;
  }

  async findPage(query: PaginationQueryDto): Promise<Client[]> {
    return this.clients.findManyPage({
      skip: query.skip,
      take: query.take,
    });
  }

  async assertExists(id: string): Promise<void> {
    const client = await this.clients.findById(id);
    if (!client) {
      throw new NotFoundException(`Client ${id} not found`);
    }
  }
}
