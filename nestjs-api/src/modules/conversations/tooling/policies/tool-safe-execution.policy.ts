export const MAX_TOOL_ATTEMPTS = 2;

export function isRecoverableToolError(err: unknown): boolean {
  if (!(err instanceof Error)) {
    return false;
  }
  return /network|timeout|econnreset|econnrefused/i.test(err.message);
}
