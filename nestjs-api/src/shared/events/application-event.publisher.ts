import type { ApplicationEvent } from './application-event';

export const APPLICATION_EVENT_PUBLISHER = Symbol('APPLICATION_EVENT_PUBLISHER');

/**
 * Outbound application event port. Implementations may be in-memory today and
 * replaced with external dispatch later without changing publishers' call sites.
 */
export interface ApplicationEventPublisher {
  publish<TPayload extends Record<string, unknown>>(
    event: Readonly<ApplicationEvent<TPayload>>,
  ): void;
}
