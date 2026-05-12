import { Injectable } from '@nestjs/common';
import { ALLOWED_FACT_SOURCE_KINDS } from '../domain/hallucination-boundaries';
import type {
  AiAssembledContext,
  AiContextAssemblyInput,
  AiContextBuilder,
} from './ai-context.builder';
import { BusinessContextRetrievalService } from '../retrieval/business-context-retrieval.service';
import { prioritizeRetrievalFactKeys } from '../retrieval/prioritization/retrieval-fact-prioritizer';
import { buildConversationMemorySnapshot } from '../conversation-memory/conversation-memory.snapshot';
import { SalesPlaybookSelector } from '../sales-playbooks/sales-playbook.selector';
import { extractSalesSignals } from '../sales-decisions/extraction/sales-signals.extractor';

function lastAssistantExcerpt(
  snapshot: AiAssembledContext['businessSnapshot'],
): string {
  const turns = snapshot?.facts['recent.messages/turns'];
  if (!Array.isArray(turns)) {
    return '';
  }
  const assistants = turns.filter(
    (t) =>
      t &&
      typeof t === 'object' &&
      (t as { role?: unknown }).role === 'ASSISTANT',
  );
  const last = assistants[assistants.length - 1] as { content?: unknown } | undefined;
  return typeof last?.content === 'string' ? last.content : '';
}

@Injectable()
export class RetrievalAiContextBuilder implements AiContextBuilder {
  constructor(
    private readonly retrieval: BusinessContextRetrievalService,
    private readonly playbookSelector: SalesPlaybookSelector,
  ) {}

  async build(input: AiContextAssemblyInput): Promise<AiAssembledContext> {
    const businessSnapshot = await this.retrieval.retrieve(input);
    const retrievalKeys = Object.keys(businessSnapshot.facts);
    const orderedBusinessFactKeys = prioritizeRetrievalFactKeys(
      businessSnapshot.facts,
    );
    const memory = buildConversationMemorySnapshot(businessSnapshot);
    const assistantExcerpt = lastAssistantExcerpt(businessSnapshot);
    const signals = extractSalesSignals({
      userText: input.userTurn?.text ?? '',
      assistantReplyText: assistantExcerpt,
      currentStage: input.currentStage,
      dialogStatus: input.dialogStatus,
    });
    const salesPlaybookSnapshot = this.playbookSelector.select({
      currentStage: input.currentStage,
      scenarioCode: input.scenarioCode,
      signals,
    });
    const baseKeys = [
      'dialogId',
      'currentStage',
      'dialogStatus',
      'channel',
      'scenarioCode',
      'conversationMemory.v1',
    ];
    const allowedFactKeys = [...new Set([...baseKeys, ...retrievalKeys])];
    return {
      dialogId: input.dialogId,
      correlationId: input.correlationId,
      currentStage: input.currentStage,
      dialogStatus: input.dialogStatus,
      channel: input.channel,
      scenarioCode: input.scenarioCode,
      userTurnText: input.userTurn?.text,
      allowedFactKeys,
      allowedFactSources: [...ALLOWED_FACT_SOURCE_KINDS],
      businessSnapshot,
      orderedBusinessFactKeys,
      salesPlaybookSnapshot,
      conversationMemory: memory,
    };
  }
}
