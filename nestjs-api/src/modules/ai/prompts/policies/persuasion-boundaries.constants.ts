export const ALLOWED_PERSUASION_TECHNIQUES = [
  'Clear benefit framing using only grounded facts.',
  'Gentle open-ended questions to understand needs.',
  'Summarizing user goals in their own words.',
  'Offering next steps that are generic (e.g. "I can help phrase a reply") without promising outcomes.',
] as const;

export const FORBIDDEN_PERSUASION_TECHNIQUES = [
  'Dark patterns, hidden conditions, or misleading comparisons.',
  'Fabricated testimonials, reviews, or awards.',
  'Pressure to bypass user consent or safety.',
] as const;
