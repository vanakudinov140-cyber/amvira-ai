import { Module } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AI_CONTEXT_BUILDER } from './context/ai-context.builder';
import { RetrievalAiContextBuilder } from './context/retrieval-ai-context.builder';
import { AI_RESPONSE_VALIDATOR } from './contracts/ai-response.validator';
import { AI_PROMPT_COMPOSER } from './prompts/ai-prompt.composer';
import { LLM_CLIENT } from './contracts/llm.client';
import { StubLlmClient } from './contracts/stub-llm.client';
import { AiOrchestrationService } from './orchestration/ai-orchestration.service';
import { DefaultAiResponseValidator } from './orchestration/default-ai-response.validator';
import { AiPolicyEvaluator } from './policies/ai-policy.evaluator';
import { GigachatLlmClient } from './providers/gigachat/gigachat-llm.client';
import { GigachatProviderModule } from './providers/gigachat/gigachat.module';
import { SalesPromptComposer } from './prompts/sales-prompt.composer';
import { ScenarioPromptRegistry } from './prompts/scenarios/scenario-prompt.registry';
import { StagePromptRegistry } from './prompts/stages/stage-prompt.registry';
import { SystemTemplateAssembler } from './prompts/templates/system-template.assembler';
import { ToneProfileRegistry } from './prompts/tones/tone-profile.registry';
import { AiSalesDecisionService } from './sales-decisions/ai-sales-decision.service';
import { SalesPlaybookSelector } from './sales-playbooks/sales-playbook.selector';
import { BusinessContextRetrievalService } from './retrieval/business-context-retrieval.service';
import { BookingSummariesBusinessContextProvider } from './retrieval/providers/booking-summaries.business-context.provider';
import { DialogSnapshotBusinessContextProvider } from './retrieval/providers/dialog-snapshot.business-context.provider';
import { RecentMessagesBusinessContextProvider } from './retrieval/providers/recent-messages.business-context.provider';
import { SalonConfigBusinessContextProvider } from './retrieval/providers/salon-config.business-context.provider';
import { ScenarioSnapshotBusinessContextProvider } from './retrieval/providers/scenario-snapshot.business-context.provider';
import { StaticCatalogBusinessContextProvider } from './retrieval/providers/static-catalog.business-context.provider';
import { GroundingSnapshotComposer } from './retrieval/snapshots/grounding-snapshot.composer';
import { YclientsAvailabilityBusinessContextProvider } from './retrieval/providers/yclients-availability.business-context.provider';
import { DialogsModule } from '../dialogs/dialogs.module';
import { MessagesModule } from '../messages/messages.module';

@Module({
  imports: [GigachatProviderModule, DialogsModule, MessagesModule],
  providers: [
    AiPolicyEvaluator,
    AiOrchestrationService,
    StubLlmClient,
    SystemTemplateAssembler,
    StagePromptRegistry,
    ScenarioPromptRegistry,
    ToneProfileRegistry,
    SalesPromptComposer,
    GroundingSnapshotComposer,
    SalesPlaybookSelector,
    StaticCatalogBusinessContextProvider,
    SalonConfigBusinessContextProvider,
    ScenarioSnapshotBusinessContextProvider,
    DialogSnapshotBusinessContextProvider,
    RecentMessagesBusinessContextProvider,
    BookingSummariesBusinessContextProvider,
    YclientsAvailabilityBusinessContextProvider,
    BusinessContextRetrievalService,
    AiSalesDecisionService,
    { provide: AI_CONTEXT_BUILDER, useClass: RetrievalAiContextBuilder },
    { provide: AI_PROMPT_COMPOSER, useClass: SalesPromptComposer },
    {
      provide: LLM_CLIENT,
      useFactory: (
        config: ConfigService,
        stub: StubLlmClient,
        gigachat: GigachatLlmClient,
      ) => {
        const key = config.get<string>('gigachat.authorizationKey', '')?.trim() ?? '';
        return key.length > 0 ? gigachat : stub;
      },
      inject: [ConfigService, StubLlmClient, GigachatLlmClient],
    },
    { provide: AI_RESPONSE_VALIDATOR, useClass: DefaultAiResponseValidator },
  ],
  exports: [AiOrchestrationService, AiPolicyEvaluator, AiSalesDecisionService],
})
export class AiModule {}
