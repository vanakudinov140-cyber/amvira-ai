export type DeliveryTelemetryV1 = {
  readonly telemetryVersion: 'delivery_telemetry@v1';
  readonly outcomeKind: string;
  readonly syncReceiptStatus?: string;
  readonly asyncAccepted?: boolean;
};
