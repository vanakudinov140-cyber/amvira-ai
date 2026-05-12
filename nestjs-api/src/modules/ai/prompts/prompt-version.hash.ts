import { createHash } from 'node:crypto';

const RELEASE = 'sales-prompts@1.0.0';

export function getPromptReleaseLabel(): string {
  return RELEASE;
}

/**
 * Stable fingerprint for tracing: block ids + release label (not full prompt body).
 */
export function computePromptVersionHash(parts: readonly string[]): string {
  return createHash('sha256')
    .update([RELEASE, ...parts].join('\u001f'))
    .digest('hex')
    .slice(0, 16);
}
