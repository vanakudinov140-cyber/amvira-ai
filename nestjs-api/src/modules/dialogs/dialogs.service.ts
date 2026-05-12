import {
  BadRequestException,
  Inject,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import {
  type Dialog,
  DialogStage as DialogStageValue,
  DialogStatus,
  type Prisma,
} from '@prisma/client';
import { DialogsRepository } from '../../infrastructure/persistence/repositories/dialogs.repository';
import { PrismaService } from '../../infrastructure/persistence/prisma.service';
import { ScenariosRepository } from '../../infrastructure/persistence/repositories/scenarios.repository';
import { ClientsService } from '../clients/clients.service';
import { CreateDialogDto } from './dto/create-dialog.dto';
import { TransitionDialogStageDto } from './dto/transition-dialog-stage.dto';
import { DialogStageTransitionDenied } from './domain/dialog-stage.errors';
import { assertStageTransitionAllowed } from './domain/dialog-stage.policy';
import { isDialogStageCode } from './domain/dialog-stage.types';
import { dialogCreatedEvent } from './events/dialog-created.event';
import { dialogStageTransitionedEvent } from './events/dialog-stage-transitioned.event';
import {
  APPLICATION_EVENT_PUBLISHER,
  type ApplicationEventPublisher,
} from '../../shared/events/application-event.publisher';

@Injectable()
export class DialogsService {
  constructor(
    private readonly clients: ClientsService,
    private readonly dialogs: DialogsRepository,
    private readonly scenarios: ScenariosRepository,
    private readonly prisma: PrismaService,
    @Inject(APPLICATION_EVENT_PUBLISHER)
    private readonly applicationEvents: ApplicationEventPublisher,
  ) {}

  async create(dto: CreateDialogDto): Promise<Dialog> {
    await this.clients.assertExists(dto.clientId);

    const scenario = await this.scenarios.findByCode(dto.scenarioCode);
    if (!scenario) {
      throw new NotFoundException(`Scenario ${dto.scenarioCode} not found`);
    }

    const dialog = await this.dialogs.createWithInitialState({
      client: { connect: { id: dto.clientId } },
      currentStage: DialogStageValue.TRUST_BUILDING,
      status: DialogStatus.ACTIVE,
      channel: dto.channel,
      scenario: { connect: { id: scenario.id } },
    });

    this.applicationEvents.publish(
      dialogCreatedEvent({
        id: dialog.id,
        clientId: dialog.clientId,
        scenarioId: dialog.scenarioId,
        channel: dialog.channel,
        currentStage: dialog.currentStage,
        status: dialog.status,
      }),
    );

    return dialog;
  }

  async findOne(id: string): Promise<Dialog> {
    const dialog = await this.dialogs.findById(id);
    if (!dialog) {
      throw new NotFoundException(`Dialog ${id} not found`);
    }
    return dialog;
  }

  /** Scenario enum string for AI / retrieval (read-only). */
  async getScenarioCodeForDialog(dialogId: string): Promise<string | undefined> {
    const dialog = await this.dialogs.findById(dialogId);
    if (!dialog) {
      return undefined;
    }
    const row = await this.prisma.scenario.findFirst({
      where: { id: dialog.scenarioId, deletedAt: null },
      select: { code: true },
    });
    return row?.code != null ? String(row.code) : undefined;
  }

  async transitionStage(
    id: string,
    dto: TransitionDialogStageDto,
  ): Promise<Dialog> {
    const dialog = await this.findOne(id);
    if (dialog.status === DialogStatus.CLOSED) {
      throw new BadRequestException('Dialog is closed');
    }
    if (dialog.currentStage === dto.stage) {
      return dialog;
    }

    const from = dialog.currentStage as string;
    const to = dto.stage as string;
    if (!isDialogStageCode(from) || !isDialogStageCode(to)) {
      throw new BadRequestException('Unknown dialog stage');
    }

    try {
      assertStageTransitionAllowed(from, to);
    } catch (err) {
      if (err instanceof DialogStageTransitionDenied) {
        throw new BadRequestException(err.message);
      }
      throw err;
    }

    const payload = dto.payload as Prisma.InputJsonValue | undefined;
    const updated = await this.dialogs.appendStateAndSetStage(
      id,
      dto.stage,
      payload,
    );

    this.applicationEvents.publish(
      dialogStageTransitionedEvent({
        dialogId: id,
        clientId: dialog.clientId,
        scenarioId: dialog.scenarioId,
        fromStage: from,
        toStage: to,
      }),
    );

    return updated;
  }
}
