import type { AiGenerationRequest } from '../contracts/ai-generation.request';
import type { SalonBusinessGroundingSnapshot } from '../retrieval/contracts/salon-grounding-snapshot.contract';
import type { AllowedFactSourceKind } from '../domain/hallucination-boundaries';
import type { SalesPlaybookSnapshotV1 } from '../sales-playbooks/sales-playbook.contract';
import type { ConversationMemorySnapshotV1 } from '../conversation-memory/conversation-memory.snapshot';

export type AiContextAssemblyInput = Readonly<
  Pick<
    AiGenerationRequest,
    | 'dialogId'
    | 'correlationId'
    | 'currentStage'
    | 'dialogStatus'
    | 'channel'
    | 'scenarioCode'
    | 'userTurn'
  >
>;

/**
 * Plain snapshot for prompt composition — never Prisma entities.
 */
export type AiAssembledContext = {
  readonly dialogId: string;
  readonly correlationId?: string;
  readonly currentStage: string;
  readonly dialogStatus: string;
  readonly channel: string;
  readonly scenarioCode?: string;
  readonly userTurnText?: string;
  /** Keys the model may treat as factual (hallucination guard). */
  readonly allowedFactKeys: readonly string[];
  readonly allowedFactSources: readonly AllowedFactSourceKind[];
  /** Composed read-only business facts for grounding (optional until retrieval runs). */
  readonly businessSnapshot?: SalonBusinessGroundingSnapshot;
  /** Priority-ordered keys for rendering retrieval JSON (recent/booking bias). */
  readonly orderedBusinessFactKeys?: readonly string[];
  /** Active sales playbook slice for prompt composition. */
  readonly salesPlaybookSnapshot?: SalesPlaybookSnapshotV1;
  /** Deterministic read-model derived from retrieval only (no AI writes). */
  readonly conversationMemory?: ConversationMemorySnapshotV1;
};

export const AI_CONTEXT_BUILDER = Symbol('AI_CONTEXT_BUILDER');

export interface AiContextBuilder {
  build(input: AiContextAssemblyInput): Promise<AiAssembledContext>;
}
