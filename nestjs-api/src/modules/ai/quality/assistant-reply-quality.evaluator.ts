import type { AiSalesDecisionEnvelope } from '../sales-decisions/contracts/ai-sales-decision.contract';

export type AssistantReplyQualityReportV1 = Readonly<{
  readonly reportVersion: 'assistant_reply_quality@v1';
  readonly verbosityScore: number;
  readonly repetitionScore: number;
  readonly bookingCtaScore: number;
  readonly hallucinationRiskScore: number;
  readonly toneConsistencyScore: number;
  readonly escalationAppropriateScore: number;
  readonly compactnessScore: number;
  readonly overallQualityScore: number;
  readonly flags: readonly string[];
}>;

const BOOKING_CTA = [
  'запис',
  'слот',
  'время',
  'когда удобно',
  'подобрать',
  'appointment',
  'book',
];

export function evaluateAssistantReplyQuality(input: {
  readonly replyText: string;
  readonly userText: string;
  readonly decision: AiSalesDecisionEnvelope;
}): AssistantReplyQualityReportV1 {
  const t = input.replyText.trim();
  const words = t.length ? t.split(/\s+/).length : 0;
  const verbosityScore = Math.max(0, 1 - Math.min(1, words / 220));

  const repetitionScore = estimateRepetition(t);

  const lower = t.toLowerCase();
  const bookingCtaScore = BOOKING_CTA.some((k) => lower.includes(k))
    ? 0.85
    : input.decision.bookingConversion.conversionLikelihood > 0.55
      ? 0.35
      : 0.2;

  const hallucinationRiskScore = estimateHallucinationRisk(t, lower);

  const toneConsistencyScore = t.length > 0 && !t.includes('как модель') ? 0.82 : 0.4;

  const escalationAppropriateScore =
    input.decision.policyOutcome === 'escalate_human' ? 0.9 : 0.75;

  const compactnessScore = Math.max(0, 1 - Math.min(1, t.length / 1200));

  const flags: string[] = [];
  if (words > 180) {
    flags.push('verbose');
  }
  if (repetitionScore > 0.55) {
    flags.push('repetitive_phrasing');
  }
  if (hallucinationRiskScore > 0.55) {
    flags.push('availability_language_risk');
  }
  if (bookingCtaScore < 0.35 && input.decision.bookingReadiness.ready) {
    flags.push('weak_booking_cta');
  }

  const overall =
    (verbosityScore +
      (1 - repetitionScore) +
      bookingCtaScore +
      (1 - hallucinationRiskScore) +
      toneConsistencyScore +
      escalationAppropriateScore +
      compactnessScore) /
    7;

  return {
    reportVersion: 'assistant_reply_quality@v1',
    verbosityScore: Number(verbosityScore.toFixed(3)),
    repetitionScore: Number(repetitionScore.toFixed(3)),
    bookingCtaScore: Number(bookingCtaScore.toFixed(3)),
    hallucinationRiskScore: Number(hallucinationRiskScore.toFixed(3)),
    toneConsistencyScore: Number(toneConsistencyScore.toFixed(3)),
    escalationAppropriateScore: Number(escalationAppropriateScore.toFixed(3)),
    compactnessScore: Number(compactnessScore.toFixed(3)),
    overallQualityScore: Number(overall.toFixed(3)),
    flags,
  };
}

function estimateRepetition(text: string): number {
  const tokens = text
    .toLowerCase()
    .replace(/[^a-zа-яё0-9\s]/gi, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 3);
  if (tokens.length < 6) {
    return 0.1;
  }
  const freq = new Map<string, number>();
  for (const w of tokens) {
    freq.set(w, (freq.get(w) ?? 0) + 1);
  }
  let max = 0;
  for (const c of freq.values()) {
    max = Math.max(max, c);
  }
  return Math.min(1, max / Math.max(8, tokens.length / 3));
}

function estimateHallucinationRisk(text: string, lower: string): number {
  let risk = 0.12;
  const risky = [
    'гарантированно свободно',
    'точно есть место',
    '100% слот',
    'уже записала вас',
    'я записал',
  ];
  if (risky.some((p) => lower.includes(p))) {
    risk += 0.45;
  }
  if (/\b\d{1,2}:\d{2}\b/.test(text) && !lower.includes('если удобно')) {
    risk += 0.12;
  }
  return Math.min(1, risk);
}
