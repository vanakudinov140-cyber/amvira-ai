import type { ApplicationEvent } from './application-event';
import type { ApplicationEventType } from './application-event-type';

/**
 * Application-layer reaction to a published {@link ApplicationEvent}.
 * Implementations perform side effects (logging, metrics hooks); they must not
 * import Prisma, mutate FSM, call repositories directly, or perform HTTP I/O.
 */
export interface ApplicationEventHandler {
  readonly eventType: ApplicationEventType;

  handle(event: Readonly<ApplicationEvent<Record<string, unknown>>>): void;
}
