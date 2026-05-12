import type { PromptBlock } from '../blocks/prompt-block.contract';

export type ToneProfileKey = 'professional_warm' | 'neutral_concise';

export type ToneProfile = {
  readonly key: ToneProfileKey;
  readonly label: string;
  readonly blocks: readonly PromptBlock[];
};

const PROFESSIONAL_WARM_BLOCKS: readonly PromptBlock[] = [
  {
    id: 'tone.professional_warm',
    lane: 'system',
    render: () =>
      [
        'Tone: professional and warm.',
        '- Use polite forms; avoid slang unless the user uses it first.',
        '- Keep empathy proportionate; avoid over-apologizing.',
      ].join('\n'),
  },
];

const NEUTRAL_CONCISE_BLOCKS: readonly PromptBlock[] = [
  {
    id: 'tone.neutral_concise',
    lane: 'system',
    render: () =>
      [
        'Tone: neutral and concise.',
        '- Prefer short sentences; minimize filler.',
      ].join('\n'),
  },
];

const PROFILES: Readonly<Record<ToneProfileKey, ToneProfile>> = {
  professional_warm: {
    key: 'professional_warm',
    label: 'Professional warm (default sales)',
    blocks: PROFESSIONAL_WARM_BLOCKS,
  },
  neutral_concise: {
    key: 'neutral_concise',
    label: 'Neutral concise',
    blocks: NEUTRAL_CONCISE_BLOCKS,
  },
};

export function resolveToneProfile(key?: string): ToneProfile {
  if (key && key in PROFILES) {
    return PROFILES[key as ToneProfileKey];
  }
  return PROFILES.professional_warm;
}
