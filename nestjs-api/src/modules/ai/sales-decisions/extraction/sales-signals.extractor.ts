import type { DialogStageCode } from '../../../dialogs/domain/dialog-stage.types';
import type {
  AiSalesDecisionInput,
  AiSalesIntentSignal,
  AiSalesLeadQualification,
  AiSalesObjectionProfile,
  AiSalesTransitionProposal,
} from '../contracts/ai-sales-decision.contract';
import { AiSalesDecisionPolicy } from '../policies/ai-sales-decision.policy';

const OBJECTION_MARKERS: ReadonlyArray<{ id: string; needles: readonly string[] }> =
  [
    {
      id: 'price',
      needles: ['дорог', 'expensive', 'цена', 'price', 'дешевле', 'cheaper'],
    },
    {
      id: 'doubt',
      needles: ['не уверен', 'сомневаюсь', 'doubt', 'not sure', 'maybe not'],
    },
    {
      id: 'refusal_soft',
      needles: ['не хочу', "don't want", 'не интересно', 'not interested'],
    },
    {
      id: 'competitor',
      needles: ['у других', 'другой салон', 'competitor', 'elsewhere'],
    },
  ];

const BOOKING_MARKERS: ReadonlyArray<{ id: string; needles: readonly string[] }> = [
  {
    id: 'book',
    needles: [
      'запис',
      'запиш',
      'appointment',
      'book',
      'слот',
      'когда можно',
      'свободн',
    ],
  },
];

const WARM_MARKERS = [
  'интересно',
  'хочу',
  'давайте',
  'ок',
  'yes',
  'подходит',
  'sounds good',
];

export type ExtractedSalesSignals = {
  intents: AiSalesIntentSignal[];
  objection: AiSalesObjectionProfile;
  leadQualification: AiSalesLeadQualification;
  bookingReadiness: {
    ready: boolean;
    score: number;
    signals: readonly string[];
  };
  overallConfidence: number;
};

export function extractSalesSignals(
  input: AiSalesDecisionInput,
): ExtractedSalesSignals {
  const blob = `${input.userText}\n${input.assistantReplyText}`.toLowerCase();
  const objectionSignals: string[] = [];
  for (const m of OBJECTION_MARKERS) {
    if (m.needles.some((n) => blob.includes(n))) {
      objectionSignals.push(m.id);
    }
  }
  const objectionDetected = objectionSignals.length > 0;
  let severity: AiSalesObjectionProfile['severity'] = 'none';
  if (objectionDetected) {
    if (objectionSignals.includes('refusal_soft') || objectionSignals.length >= 3) {
      severity = 'high';
    } else if (objectionSignals.length >= 2) {
      severity = 'medium';
    } else {
      severity = 'low';
    }
  }

  const bookingSignals: string[] = [];
  for (const m of BOOKING_MARKERS) {
    if (m.needles.some((n) => blob.includes(n))) {
      bookingSignals.push(m.id);
    }
  }
  const bookingScore = Math.min(1, bookingSignals.length * 0.45 + blob.length / 800);

  const warmHits = WARM_MARKERS.filter((w) => blob.includes(w)).length;
  const leadScore = Math.min(
    1,
    warmHits * 0.2 + (objectionDetected ? 0.1 : 0.25) + bookingScore * 0.35,
  );
  let level: AiSalesLeadQualification['level'] = 'cold';
  if (leadScore > 0.65) {
    level = 'hot';
  } else if (leadScore > 0.35) {
    level = 'warm';
  }

  const intents: AiSalesIntentSignal[] = [
    {
      label: 'objection',
      score: objectionDetected ? 0.55 + objectionSignals.length * 0.12 : 0.05,
    },
    {
      label: 'booking_interest',
      score: bookingScore,
    },
    {
      label: 'qualification',
      score: Math.min(1, input.userText.length / 400),
    },
    {
      label: 'smalltalk',
      score: blob.includes('привет') || blob.includes('hello') ? 0.4 : 0.08,
    },
    {
      label: 'informational',
      score: 0.25,
    },
    { label: 'unknown', score: 0.05 },
  ].sort((a, b) => b.score - a.score) as AiSalesIntentSignal[];

  const overallConfidence = Math.min(
    1,
    Math.max(intents[0]?.score ?? 0, bookingScore, leadScore),
  );

  return {
    intents,
    objection: {
      detected: objectionDetected,
      severity,
      signals: objectionSignals,
    },
    leadQualification: {
      level,
      score: leadScore,
      signals: warmHits > 0 ? ['positive_markers'] : [],
    },
    bookingReadiness: {
      ready: bookingScore > 0.55,
      score: bookingScore,
      signals: bookingSignals,
    },
    overallConfidence,
  };
}

export function recommendStage(
  current: DialogStageCode,
  signals: ExtractedSalesSignals,
  policy: AiSalesDecisionPolicy,
): {
  recommended: DialogStageCode | null;
  proposal: AiSalesTransitionProposal | null;
} {
  if (signals.objection.detected && signals.objection.severity !== 'none') {
    const target: DialogStageCode = 'OBJECTION_HANDLING';
    const proposal = policy.proposeTransition(current, target, 'objection_signals');
    return { recommended: proposal?.toStage ?? null, proposal };
  }
  if (signals.bookingReadiness.ready) {
    const target: DialogStageCode = 'BOOKING';
    const proposal = policy.proposeTransition(current, target, 'booking_readiness');
    return { recommended: proposal?.toStage ?? null, proposal };
  }
  if (signals.leadQualification.level === 'hot' && signals.overallConfidence > 0.55) {
    const idx = ['TRUST_BUILDING', 'DISCOVERY', 'PRESENTATION'].indexOf(current);
    if (idx >= 0 && idx <= 2) {
      const target = ['DISCOVERY', 'PRESENTATION', 'BOOKING'][idx] as DialogStageCode;
      const proposal = policy.proposeTransition(current, target, 'lead_hot_forward');
      return { recommended: proposal?.toStage ?? null, proposal };
    }
  }
  return { recommended: null, proposal: null };
}
