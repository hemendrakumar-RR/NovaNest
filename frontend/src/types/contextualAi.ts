export interface ContextualAIPayload {
  dashboardName: string;
  kpiOrChartId: string;
  selectedMetric?: string;
  metricValue?: string | number;
  activeFilters?: Record<string, any>;
  city?: string;
  dateRange?: string;
  entityType?: 'customer' | 'restaurant' | 'rider' | 'order' | 'segment';
  entityId?: string;
  entityName?: string;
  sourceComponent?: string;
  suggestedPrompt?: string;
  autoSubmit?: boolean;
}

export function buildContextualPrompt(payload: ContextualAIPayload): string {
  if (payload.suggestedPrompt) {
    return payload.suggestedPrompt;
  }

  const citySuffix = payload.city && payload.city !== 'All' ? ` in ${payload.city}` : '';

  if (payload.entityType === 'customer' && payload.entityId) {
    const namePart = payload.entityName ? ` (${payload.entityName})` : '';
    return `Analyze customer profile for ${payload.entityId}${namePart}${citySuffix}, including order history, RFM tier, and churn risk.`;
  }

  if (payload.entityType === 'restaurant' && (payload.entityName || payload.entityId)) {
    const restName = payload.entityName || payload.entityId;
    return `Analyze restaurant performance and early warning risks for "${restName}"${citySuffix}.`;
  }

  if (payload.entityType === 'rider' && payload.entityId) {
    return `Analyze delivery latency, SLA breach rate, and dispatch efficiency for rider ${payload.entityId}${citySuffix}.`;
  }

  if (payload.selectedMetric) {
    return `Analyze ${payload.selectedMetric}${citySuffix} on the ${payload.dashboardName} dashboard.`;
  }

  return `Analyze ${payload.kpiOrChartId.replace(/_/g, ' ')}${citySuffix} from ${payload.dashboardName}.`;
}

export function launchContextualAI(payload: ContextualAIPayload) {
  const prompt = buildContextualPrompt(payload);
  const event = new CustomEvent('novanest-launch-contextual-ai', {
    detail: {
      payload,
      prompt,
    },
  });
  window.dispatchEvent(event);
}

