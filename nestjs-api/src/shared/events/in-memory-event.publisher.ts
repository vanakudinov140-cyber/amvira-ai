import { Injectable, Logger } from '@nestjs/common';
import type { ApplicationEvent } from './application-event';
import type { ApplicationEventPublisher } from './application-event.publisher';

type Handler = (event: Readonly<ApplicationEvent<Record<string, unknown>>>) => void;

/**
 * Synchronous in-process fan-out. No queues, no persistence, no retries.
 * Subscribe via this class in composition roots / tests; services depend only on
 * {@link ApplicationEventPublisher}.
 */
@Injectable()
export class InMemoryApplicationEventPublisher implements ApplicationEventPublisher {
  private readonly logger = new Logger(InMemoryApplicationEventPublisher.name);
  private readonly handlers = new Map<string, Set<Handler>>();

  publish<TPayload extends Record<string, unknown>>(
    event: Readonly<ApplicationEvent<TPayload>>,
  ): void {
    const list = this.handlers.get(event.type);
    if (!list || list.size === 0) {
      return;
    }
    for (const handler of list) {
      try {
        handler(event as Readonly<ApplicationEvent<Record<string, unknown>>>);
      } catch (err) {
        this.logger.error(
          `Application event subscriber failed (type=${event.type})`,
          err instanceof Error ? err.stack : err,
        );
      }
    }
  }

  /**
   * Returns an unsubscribe function. Intended for future orchestration wiring, not for services.
   */
  subscribe<TPayload extends Record<string, unknown>>(
    eventType: ApplicationEvent<TPayload>['type'],
    handler: (event: Readonly<ApplicationEvent<TPayload>>) => void,
  ): () => void {
    const wrapped: Handler = (e) =>
      handler(e as Readonly<ApplicationEvent<TPayload>>);
    let set = this.handlers.get(eventType);
    if (!set) {
      set = new Set();
      this.handlers.set(eventType, set);
    }
    set.add(wrapped);
    return () => {
      const current = this.handlers.get(eventType);
      current?.delete(wrapped);
      if (current && current.size === 0) {
        this.handlers.delete(eventType);
      }
    };
  }
}
