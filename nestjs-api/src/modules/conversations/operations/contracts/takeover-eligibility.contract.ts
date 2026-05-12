import type { AssistantSuspensionMode } from '../contracts/takeover.contract';

export type TakeoverEligibilityV1 = {
  readonly eligibilityVersion: 'takeover_eligibility@v1';
  readonly takeoverAllowed: boolean;
  readonly suggestedSuspension: AssistantSuspensionMode;
  readonly rationale: string;
};
