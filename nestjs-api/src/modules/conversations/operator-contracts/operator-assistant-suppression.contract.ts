/**
 * Advisory suppression relative to assistant outbound — carried transiently for gateways.
 */
export type OperatorAssistantSuppressionSignalV1 = {
  readonly suppressionVersion: 'operator_assistant_suppression@v1';
  readonly suggestHoldAssistantOutbound: boolean;
};
