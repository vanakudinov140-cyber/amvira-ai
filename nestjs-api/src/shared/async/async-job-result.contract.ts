/**
 * Ack from dispatcher — not execution result of the job body.
 */
export type AsyncJobDispatchResult = {
  readonly accepted: boolean;
  readonly jobId: string;
  readonly detail?: string;
};

/**
 * Future: result of job execution (returned by worker), kept separate from dispatch ack.
 */
export type AsyncJobExecutionResult<TResult = unknown> = {
  readonly jobId: string;
  readonly ok: boolean;
  readonly result?: TResult;
  readonly errorCode?: string;
};
