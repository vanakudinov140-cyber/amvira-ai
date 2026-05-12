import type {
  AiSalesBookingReadiness,
  AiSalesLeadQualification,
  AiSalesObjectionProfile,
  BookingConversionOptimizationV1,
  ObjectionCategory,
  ObjectionIntelligenceV1,
  ObjectionRecoveryStrategy,
} from './contracts/ai-sales-decision.contract';

const PRICE = ['price', 'дорог', 'дешев', 'сколько стоит', 'цена'];
const TRUST = ['не довер', 'страшно', 'боюсь', 'trust', 'reviews', 'отзыв'];
const TIMING = ['потом', 'позже', 'нет времени', 'busy', 'неделя', 'месяц'];
const HESITATION = ['не знаю', 'не уверен', 'maybe', 'думаю'];
const COMPARISON = ['competitor', 'у других', 'другой салон', 'сравни'];

export function buildObjectionIntelligence(input: {
  readonly objection: AiSalesObjectionProfile;
  readonly userText: string;
  readonly lead: AiSalesLeadQualification;
  readonly booking: AiSalesBookingReadiness;
}): ObjectionIntelligenceV1 {
  const blob = input.userText.toLowerCase();
  const cats: ObjectionCategory[] = [];
  const push = (c: ObjectionCategory, needles: readonly string[]) => {
    if (needles.some((n) => blob.includes(n))) {
      cats.push(c);
    }
  };
  push('price', PRICE);
  push('trust', TRUST);
  push('timing', TIMING);
  push('hesitation', HESITATION);
  push('comparison', COMPARISON);
  if (blob.trim().length < 3) {
    cats.push('no_response');
  }
  for (const s of input.objection.signals) {
    if (s === 'price') {
      cats.push('price');
    }
    if (s === 'doubt' || s === 'refusal_soft') {
      cats.push('hesitation');
    }
    if (s === 'competitor') {
      cats.push('comparison');
    }
  }
  const uniq = [...new Set(cats)];
  let primary: ObjectionCategory | null = null;
  if (input.objection.detected) {
    primary = uniq[0] ?? 'unclear_need';
  } else if (input.booking.score < 0.2 && blob.length < 8) {
    primary = 'unclear_need';
  }

  let recovery: ObjectionRecoveryStrategy = 'pace_control';
  if (primary === 'price') {
    recovery = 'reframe_value';
  } else if (primary === 'trust') {
    recovery = 'social_proof_light';
  } else if (primary === 'timing') {
    recovery = 'reduce_commitment';
  } else if (primary === 'comparison') {
    recovery = 'reframe_value';
  } else if (primary === 'hesitation') {
    recovery = 'empathy_clarify';
  }

  let escalationThreshold = 0.28;
  if (input.objection.severity === 'high') {
    escalationThreshold = 0.45;
  } else if (input.objection.severity === 'medium') {
    escalationThreshold = 0.35;
  }
  if (input.lead.level === 'cold') {
    escalationThreshold += 0.05;
  }

  return {
    version: 'objection_intelligence@v1',
    primaryCategory: primary,
    secondaryCategories: uniq.filter((c) => c !== primary).slice(0, 3),
    severity: input.objection.severity,
    recoveryStrategy: recovery,
    escalationThreshold,
  };
}

export function buildBookingConversionOptimization(input: {
  readonly booking: AiSalesBookingReadiness;
  readonly lead: AiSalesLeadQualification;
  readonly objection: AiSalesObjectionProfile;
  readonly intentsTopLabel: string;
}): BookingConversionOptimizationV1 {
  const mom =
    input.booking.score * 0.55 +
    input.lead.score * 0.35 +
    (input.objection.detected ? -0.15 : 0.1);
  const momentum = Math.max(0, Math.min(1, mom));
  const conversion = Math.max(
    0,
    Math.min(
      1,
      input.booking.score * 0.65 +
        input.lead.score * 0.25 -
        (input.objection.severity === 'high' ? 0.2 : 0),
    ),
  );

  let next: BookingConversionOptimizationV1['nextBestAction'] = 'soft_nudge';
  if (input.objection.detected && input.objection.severity !== 'none') {
    next = 'handle_objection';
  } else if (input.booking.ready) {
    next = 'confirm_slot';
  } else if (input.intentsTopLabel === 'qualification') {
    next = 'clarify_service';
  } else if (input.booking.score > 0.45) {
    next = 'collect_contact';
  } else if (momentum < 0.25) {
    next = 'hold';
  }

  return {
    version: 'booking_conversion@v1',
    nextBestAction: next,
    bookingMomentumScore: Number(momentum.toFixed(3)),
    leadTemperature: input.lead.level,
    conversionLikelihood: Number(conversion.toFixed(3)),
  };
}
