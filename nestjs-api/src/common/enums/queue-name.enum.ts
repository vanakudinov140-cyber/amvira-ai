export enum QueueName {
  Default = 'default',
  /** External side-effects (channel delivery, …) — not application events. */
  AsyncJobs = 'async-jobs',
}
