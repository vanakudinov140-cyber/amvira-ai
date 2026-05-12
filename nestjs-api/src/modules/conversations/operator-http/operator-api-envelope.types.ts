import type { OffsetPaginationMetaV1 } from '../operator-dto/operator-pagination.dto';

export type OperatorApiErrorBodyV1 = {
  readonly errorVersion: 'operator_api_error@v1';
  readonly status: number;
  readonly code: string;
  readonly message: string;
  readonly details?: readonly string[];
};

export type OperatorApiEnvelopeV1<T> = {
  readonly apiVersion: 'operator.http@v1';
  readonly data: T;
  readonly meta?: OffsetPaginationMetaV1;
};
