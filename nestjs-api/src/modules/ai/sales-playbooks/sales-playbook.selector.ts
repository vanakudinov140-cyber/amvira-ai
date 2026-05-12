import { Injectable } from '@nestjs/common';
import type { ExtractedSalesSignals } from '../sales-decisions/extraction/sales-signals.extractor';
import { BOOKING_CONVERSION_DEFAULT_PLAYBOOK } from './booking-conversion/booking-conversion-default.playbook';
import { DISCOVERY_DEFAULT_PLAYBOOK } from './discovery/discovery-default.playbook';
import { OBJECTION_HANDLING_DEFAULT_PLAYBOOK } from './objection-handling/objection-handling-default.playbook';
import { QUALIFICATION_DEFAULT_PLAYBOOK } from './qualification/qualification-default.playbook';
import { REACTIVATION_DEFAULT_PLAYBOOK } from './reactivation/reactivation-default.playbook';
import { RETENTION_DEFAULT_PLAYBOOK } from './retention/retention-default.playbook';
import type {
  SalesPlaybookDefinition,
  SalesPlaybookSnapshotV1,
} from './sales-playbook.contract';

export type SalesPlaybookSelectionInput = Readonly<{
  readonly currentStage: string;
  readonly scenarioCode?: string;
  readonly signals: ExtractedSalesSignals;
}>;

@Injectable()
export class SalesPlaybookSelector {
  select(input: SalesPlaybookSelectionInput): SalesPlaybookSnapshotV1 {
    const rationale: string[] = [];
    const supporting: SalesPlaybookDefinition[] = [];

    const scenario = (input.scenarioCode ?? '').toUpperCase();
    if (scenario.includes('REACTIVATION')) {
      supporting.push(REACTIVATION_DEFAULT_PLAYBOOK);
      rationale.push('scenario_reactivation_bias');
    }
    if (scenario.includes('RETENTION')) {
      supporting.push(RETENTION_DEFAULT_PLAYBOOK);
      rationale.push('scenario_retention_bias');
    }

    let primary: SalesPlaybookDefinition = DISCOVERY_DEFAULT_PLAYBOOK;
    if (input.signals.objection.detected && input.signals.objection.severity !== 'none') {
      primary = OBJECTION_HANDLING_DEFAULT_PLAYBOOK;
      rationale.push('objection_signals');
    } else if (input.signals.bookingReadiness.ready) {
      primary = BOOKING_CONVERSION_DEFAULT_PLAYBOOK;
      rationale.push('booking_readiness_high');
    } else if (input.signals.leadQualification.level === 'hot') {
      primary = BOOKING_CONVERSION_DEFAULT_PLAYBOOK;
      rationale.push('lead_hot');
    } else if (
      input.currentStage === 'DISCOVERY' ||
      input.currentStage === 'TRUST_BUILDING'
    ) {
      primary = DISCOVERY_DEFAULT_PLAYBOOK;
      rationale.push('stage_discovery_trust');
    } else if (input.currentStage === 'PRESENTATION') {
      primary = QUALIFICATION_DEFAULT_PLAYBOOK;
      rationale.push('stage_presentation');
    } else if (input.currentStage === 'OBJECTION_HANDLING') {
      primary = OBJECTION_HANDLING_DEFAULT_PLAYBOOK;
      rationale.push('stage_objection');
    } else if (input.currentStage === 'BOOKING') {
      primary = BOOKING_CONVERSION_DEFAULT_PLAYBOOK;
      rationale.push('stage_booking');
    } else {
      rationale.push('default_discovery');
    }

    if (
      primary.id !== OBJECTION_HANDLING_DEFAULT_PLAYBOOK.id &&
      input.signals.objection.detected
    ) {
      supporting.push(OBJECTION_HANDLING_DEFAULT_PLAYBOOK);
    }
    if (
      primary.id !== QUALIFICATION_DEFAULT_PLAYBOOK.id &&
      ['PRESENTATION', 'DISCOVERY'].includes(input.currentStage)
    ) {
      supporting.push(QUALIFICATION_DEFAULT_PLAYBOOK);
    }

    const dedup = new Map<string, SalesPlaybookDefinition>();
    for (const p of supporting) {
      dedup.set(p.id, p);
    }
    dedup.delete(primary.id);

    return {
      snapshotVersion: 'sales_playbook@v1',
      primary,
      supporting: [...dedup.values()].slice(0, 2),
      selectionRationale: rationale,
    };
  }
}
