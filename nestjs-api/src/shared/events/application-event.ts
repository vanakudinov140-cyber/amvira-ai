import type { ApplicationEventType } from './application-event-type';

/**
 * Optional orchestration metadata (correlation, tracing). Must never carry Prisma
 * entities, HTTP context, or integration payloads — keep it transport-oriented.
 */
export type ApplicationEventMeta = {
  correlationId?: string;
};

/**
 * Base application event envelope.
 *
 * Payload boundaries:
 * - Put only domain-stable fields (ids, enum labels as strings, timestamps as ISO).
 * - Do not pass Prisma models, class instances, or Request/Response objects.
 */
export type ApplicationEvent<TPayload extends Record<string, unknown>> = {
  readonly type: ApplicationEventType;
  readonly occurredAt: Date;
  readonly payload: Readonly<TPayload>;
  readonly meta?: ApplicationEventMeta;
};
