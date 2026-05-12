import { Inject, Injectable, Logger, OnModuleInit } from '@nestjs/common';
import type { ApplicationEventHandler } from './application-event.handler';
import { InMemoryApplicationEventPublisher } from './in-memory-event.publisher';

/** Multi-provider token: all {@link ApplicationEventHandler} beans. */
export const APPLICATION_EVENT_HANDLERS = Symbol('APPLICATION_EVENT_HANDLERS');

/**
 * Single composition-root registration: wires handlers to the in-memory bus by
 * {@link ApplicationEventHandler.eventType}. Dispatch remains synchronous; the
 * bus isolates subscriber failures from the publisher call stack.
 */
@Injectable()
export class ApplicationEventHandlerRegistry implements OnModuleInit {
  private readonly logger = new Logger(ApplicationEventHandlerRegistry.name);

  constructor(
    private readonly bus: InMemoryApplicationEventPublisher,
    @Inject(APPLICATION_EVENT_HANDLERS)
    private readonly handlers: ApplicationEventHandler[],
  ) {}

  onModuleInit(): void {
    for (const handler of this.handlers) {
      this.bus.subscribe(handler.eventType, (event) => {
        handler.handle(event);
      });
      this.logger.log(
        `Application event handler registered for type "${handler.eventType}"`,
      );
    }
  }
}
