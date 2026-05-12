import { Injectable } from '@nestjs/common';
import type { SalesToolExecutor } from '../contracts/sales-tool-executor.contract';
import type { SalesToolId } from '../contracts/tool-intent.contract';
import { BookingCreateRequestExecutor } from '../executors/booking-create-request.executor';
import { EscalationHandoffExecutor } from '../executors/escalation-handoff.executor';
import { FollowUpContractExecutor } from '../executors/follow-up-contract.executor';

@Injectable()
export class SalesToolRegistry {
  private readonly byId = new Map<SalesToolId, SalesToolExecutor>();

  constructor(
    booking: BookingCreateRequestExecutor,
    escalation: EscalationHandoffExecutor,
    followUp: FollowUpContractExecutor,
  ) {
    this.byId.set(booking.toolId, booking);
    this.byId.set(escalation.toolId, escalation);
    this.byId.set(followUp.toolId, followUp);
  }

  get(toolId: SalesToolId): SalesToolExecutor | undefined {
    return this.byId.get(toolId);
  }
}
