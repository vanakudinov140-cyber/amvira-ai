import type { OperatorActionOrchestrationResultV1 } from '../operator-actions/operator-action-result.contract';
import type { OperatorApiEnvelopeV1 } from '../operator-http/operator-api-envelope.types';

export function presentOperatorActionResult(
  result: OperatorActionOrchestrationResultV1,
): OperatorApiEnvelopeV1<OperatorActionOrchestrationResultV1> {
  return { apiVersion: 'operator.http@v1', data: result };
}
