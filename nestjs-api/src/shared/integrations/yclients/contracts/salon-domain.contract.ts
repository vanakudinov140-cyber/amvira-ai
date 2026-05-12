/**
 * Normalized salon catalog / booking view — not Prisma; stable for AI grounding.
 */
export type SalonServiceV1 = {
  readonly version: 'salon.service@v1';
  readonly externalId: string;
  readonly title: string;
  readonly durationMinutes?: number;
  readonly categoryTitle?: string;
};

export type SalonStaffMemberV1 = {
  readonly version: 'salon.staff@v1';
  readonly externalId: string;
  readonly displayName: string;
  readonly specialization?: string;
};

export type SalonAvailabilitySlotV1 = {
  readonly version: 'salon.availability_slot@v1';
  readonly startAtIso: string;
  readonly endAtIso?: string;
  readonly staffExternalId?: string;
  readonly serviceExternalId?: string;
};

export type SalonBookingRequestV1 = {
  readonly version: 'salon.booking_request@v1';
  readonly serviceExternalId?: string;
  readonly staffExternalId?: string;
  readonly startAtIso: string;
  readonly comment?: string;
};

export type SalonBookingResultV1 = {
  readonly version: 'salon.booking_result@v1';
  readonly externalRecordId: string;
  readonly status: string;
  readonly raw?: Readonly<Record<string, unknown>>;
};

export type SalonCustomerV1 = {
  readonly version: 'salon.customer@v1';
  readonly externalId: string;
  readonly displayName: string;
  readonly phone?: string;
};
