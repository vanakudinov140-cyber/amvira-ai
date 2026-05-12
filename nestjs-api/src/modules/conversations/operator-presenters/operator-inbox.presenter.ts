import type { OperatorInboxRowV1 } from '../read-models/operator-inbox-row.read-model';
import type {
  OperatorApiEnvelopeV1,
} from '../operator-http/operator-api-envelope.types';
import type { OffsetPaginationMetaV1 } from '../operator-dto/operator-pagination.dto';

export function presentOperatorInboxRow(
  row: OperatorInboxRowV1,
): OperatorApiEnvelopeV1<OperatorInboxRowV1> {
  return { apiVersion: 'operator.http@v1', data: row };
}

export function presentOperatorInboxPreview(
  rows: readonly OperatorInboxRowV1[],
  meta: OffsetPaginationMetaV1,
): OperatorApiEnvelopeV1<readonly OperatorInboxRowV1[]> {
  return { apiVersion: 'operator.http@v1', data: rows, meta };
}
