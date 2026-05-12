/**
 * Channel capability contract — transport limits, no Prisma.
 */
export type ChannelCapabilities = {
  readonly maxBodyLength: number;
  readonly supportsRichText: boolean;
  readonly supportsButtons: boolean;
};
