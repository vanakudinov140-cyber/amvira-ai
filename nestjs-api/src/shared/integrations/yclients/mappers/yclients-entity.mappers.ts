import type {
  SalonAvailabilitySlotV1,
  SalonBookingResultV1,
  SalonCustomerV1,
  SalonServiceV1,
  SalonStaffMemberV1,
} from '../contracts/salon-domain.contract';

export function unwrapYclientsData<T = unknown>(raw: T): unknown {
  if (raw && typeof raw === 'object' && 'data' in (raw as object)) {
    return (raw as unknown as { data: unknown }).data;
  }
  return raw;
}

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v)
    ? (v as Record<string, unknown>)
    : null;
}

export function mapYclientsServiceRow(row: unknown): SalonServiceV1 | null {
  const o = asRecord(row);
  if (!o) {
    return null;
  }
  const id = o.id;
  if (typeof id !== 'number' && typeof id !== 'string') {
    return null;
  }
  const title =
    (typeof o.title === 'string' && o.title) ||
    (typeof o.booking_title === 'string' && o.booking_title) ||
    (typeof o.name === 'string' && o.name) ||
    '';
  const rawLen = o.time ?? o.length ?? o.seance_length;
  let durationMinutes: number | undefined;
  if (typeof rawLen === 'number' && rawLen > 0) {
    durationMinutes = rawLen > 200 ? Math.round(rawLen / 60) : rawLen;
  }
  const cat = o.category;
  const catRec = asRecord(cat);
  const categoryTitle =
    typeof o.category_title === 'string'
      ? o.category_title
      : catRec && typeof catRec.title === 'string'
        ? catRec.title
        : undefined;
  return {
    version: 'salon.service@v1',
    externalId: String(id),
    title: title || `service_${id}`,
    durationMinutes,
    categoryTitle,
  };
}

export function mapYclientsStaffRow(row: unknown): SalonStaffMemberV1 | null {
  const o = asRecord(row);
  if (!o) {
    return null;
  }
  const id = o.id;
  if (typeof id !== 'number' && typeof id !== 'string') {
    return null;
  }
  const displayName =
    (typeof o.name === 'string' && o.name) ||
    (typeof o.display_name === 'string' && o.display_name) ||
    `staff_${id}`;
  const specialization =
    typeof o.specialization === 'string'
      ? o.specialization
      : typeof o.position === 'string'
        ? o.position
        : undefined;
  return {
    version: 'salon.staff@v1',
    externalId: String(id),
    displayName,
    specialization,
  };
}

function toIsoFromYclientsDatetime(s: string): string | null {
  const normalized = s.includes('T') ? s : s.replace(' ', 'T');
  const d = new Date(normalized);
  if (Number.isNaN(d.getTime())) {
    return null;
  }
  return d.toISOString();
}

export function extractDatetimeStringsFromBookTimes(raw: unknown): string[] {
  const unwrapped = unwrapYclientsData(raw);
  const out: string[] = [];

  const pushMaybe = (v: unknown) => {
    if (typeof v === 'string' && v.trim().length > 0) {
      out.push(v.trim());
    }
  };

  const walk = (node: unknown) => {
    if (node == null) {
      return;
    }
    if (typeof node === 'string') {
      pushMaybe(node);
      return;
    }
    if (Array.isArray(node)) {
      for (const it of node) {
        walk(it);
      }
      return;
    }
    const o = asRecord(node);
    if (!o) {
      return;
    }
    for (const k of ['datetime', 'date', 'time', 'start', 'start_time']) {
      pushMaybe(o[k]);
    }
    for (const k of ['times', 'seances', 'slots', 'items', 'data']) {
      if (o[k] !== undefined) {
        walk(o[k]);
      }
    }
  };

  walk(unwrapped);
  return [...new Set(out)];
}

export function mapBookTimesToSlots(
  raw: unknown,
  staffExternalId: string,
  serviceExternalId: string,
): readonly SalonAvailabilitySlotV1[] {
  const strings = extractDatetimeStringsFromBookTimes(raw);
  const slots: SalonAvailabilitySlotV1[] = [];
  for (const s of strings) {
    const iso = toIsoFromYclientsDatetime(s);
    if (!iso) {
      continue;
    }
    slots.push({
      version: 'salon.availability_slot@v1',
      startAtIso: iso,
      staffExternalId,
      serviceExternalId,
    });
  }
  return slots;
}

export function mapRecordCreateToSalonBookingResult(
  raw: unknown,
): SalonBookingResultV1 {
  const unwrapped = unwrapYclientsData(raw);
  const o = asRecord(unwrapped) ?? asRecord(raw);
  const rawId = o?.id ?? o?.record_id ?? o?.recordId;
  const id = rawId != null ? String(rawId) : 'unknown';
  const status =
    o && typeof o.attendance === 'number'
      ? String(o.attendance)
      : o && typeof o.visit_attendance === 'number'
        ? String(o.visit_attendance)
        : 'created';
  return {
    version: 'salon.booking_result@v1',
    externalRecordId: id,
    status,
    raw: o ? { ...o } : undefined,
  };
}

export function mapYclientsClientRow(row: unknown): SalonCustomerV1 | null {
  const o = asRecord(row);
  if (!o) {
    return null;
  }
  const id = o.id;
  if (typeof id !== 'number' && typeof id !== 'string') {
    return null;
  }
  const displayName =
    (typeof o.name === 'string' && o.name) ||
    (typeof o.display_name === 'string' && o.display_name) ||
    `client_${id}`;
  const phone =
    typeof o.phone === 'string'
      ? o.phone
      : typeof o.phone_string === 'string'
        ? o.phone_string
        : undefined;
  return {
    version: 'salon.customer@v1',
    externalId: String(id),
    displayName,
    phone,
  };
}
