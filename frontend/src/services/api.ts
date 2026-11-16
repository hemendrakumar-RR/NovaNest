/**
 * NovaNest Enterprise REST API Service Client
 */

const API_BASE =
  ((import.meta as any)?.env?.VITE_API_BASE as string | undefined) ||
  (typeof window !== "undefined" ? "/api" : "http://localhost:8001/api");
const TOKEN_STORAGE_KEY = "novanest_api_token";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, message: string, detail = "") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail || message;
  }
}

export function getApiToken(): string {
  try {
    const stored = typeof window !== "undefined" ? window.sessionStorage.getItem(TOKEN_STORAGE_KEY) : "";
    if (stored && stored.trim()) return stored.trim();
  } catch {
    // sessionStorage may be restricted in non-browser test environments
  }
  const envToken = (import.meta as any)?.env?.VITE_NOVANEST_API_KEY as string | undefined;
  return envToken ? envToken.trim() : "test-operator-key-phase06-8";
}

export function setApiToken(token: string): void {
  try {
    if (typeof window !== "undefined") {
      const cleaned = token.trim();
      if (cleaned) {
        window.sessionStorage.setItem(TOKEN_STORAGE_KEY, cleaned);
      } else {
        window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      }
    }
  } catch {
    // Ignore storage quota / privacy mode errors
  }
}

export function clearApiToken(): void {
  try {
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch {
    // Ignore
  }
}

export interface GlobalFilterParams {
  city?: string;
  start_date?: string;
  end_date?: string;
  restaurant_id?: string;
  customer_segment?: string;
  order_status?: string;
  payment_method?: string;
}

export function buildQueryString(params?: GlobalFilterParams | string): string {
  if (!params) return "";
  if (typeof params === "string") {
    return params && params !== "All" ? `?city=${encodeURIComponent(params)}` : "";
  }
  const sp = new URLSearchParams();
  if (params.city && params.city !== "All") sp.set("city", params.city);
  if (params.start_date) sp.set("start_date", params.start_date);
  if (params.end_date) sp.set("end_date", params.end_date);
  if (params.restaurant_id && params.restaurant_id !== "All") sp.set("restaurant_id", params.restaurant_id);
  if (params.customer_segment && params.customer_segment !== "All") sp.set("customer_segment", params.customer_segment);
  if (params.order_status && params.order_status !== "All") sp.set("order_status", params.order_status);
  if (params.payment_method && params.payment_method !== "All") sp.set("payment_method", params.payment_method);
  const q = sp.toString();
  return q ? `?${q}` : "";
}

export interface KpiCardDetail {
  label: string;
  value: number;
  previous_value: number;
  percentage_change: number;
  trend_direction: 'up' | 'down' | 'neutral';
  calculation_tooltip: string;
  data_freshness: string;
}

export interface OverviewData {
  kpis: {
    total_gmv: number;
    total_orders: number;
    delivered_orders?: number;
    active_customers: number;
    active_restaurants: number;
    active_riders?: number;
    avg_order_value: number;
    gross_aov?: number;
    fulfillment_rate_pct: number;
    delivery_success_rate?: number;
    net_platform_revenue: number;
    realized_operating_profit?: number;
    contribution_margin_pct?: number;
    take_rate_pct?: number;
    health_score: number;
    avg_rating?: number | null;
  };
  kpi_cards?: Record<string, KpiCardDetail>;
  revenue_trend: Array<{ date: string; revenue: number; net_revenue?: number; orders: number }>;
  city_breakdown: Array<{ city: string; revenue: number; orders: number }>;
  top_restaurants: Array<{
    restaurant_id: string;
    name: string;
    city: string;
    cuisine: string;
    revenue: number;
    orders: number;
    rating: number;
  }>;
  active_filters?: Record<string, any>;
  data_source: string;
}

export interface CustomerData {
  kpis: {
    total_customers: number;
    avg_aov: number;
    high_churn_rate_pct: number;
    high_risk_customers?: number;
    avg_clv_12m: number;
  };
  rfm_segments: Array<{
    segment: string;
    count: number;
    avg_monetary: number;
    avg_frequency: number;
    avg_recency: number;
  }>;
  clv_tiers: Array<{
    tier: string;
    count: number;
    avg_clv: number;
    total_clv: number;
  }>;
  churn_distribution: Array<{
    risk_level: string;
    count: number;
    percentage: number;
  }>;
  churn_data_status?: string;
  cohort_retention: Array<{
    cohort: string;
    month_0: number;
    month_1: number;
    month_2: number;
    month_3: number;
    month_4: number;
    month_5: number;
  }>;
  acquisition_trends?: Array<{
    month: string;
    new_customers: number;
  }>;
  new_vs_repeat?: {
    new_orders: number;
    repeat_orders: number;
    repeat_percentage: number;
    total_orders: number;
  };
  high_value_customers?: Array<{
    customer_id: string;
    customer_name: string;
    city: string;
    persona: string;
    estimated_clv: number;
    clv_segment: string;
    total_orders: number;
    total_revenue: number;
    aov: number;
  }>;
  active_filters?: Record<string, any>;
}

export interface CustomerListItem {
  customer_id: string;
  customer_name: string;
  city: string | null;
  order_count: number;
  total_spend: number;
  churn_risk: string | null;
  churn_probability: number | null;
  churn_probability_status?: string;
}

export interface Customer360Data {
  customer_id: string;
  name: string;
  customer_name?: string;
  email: string | null;
  city: string;
  profile: any;
  digital_twin: any;
  order_history: Array<{
    order_id: string;
    restaurant_name: string;
    datetime: string;
    amount: number;
    status: string;
  }>;
  recommendations: Array<{
    item_id: string;
    item_name: string;
    cuisine: string;
    price: number;
    score: number;
    explanation: string;
  }>;
}

export interface RestaurantData {
  kpis: {
    total_restaurants: number;
    avg_health_score: number;
    critical_risk_count: number;
    active_early_warnings: number;
  };
  health_distribution: Array<{ tier: string; count: number }>;
  risk_distribution: Array<{ risk_level: string; count: number }>;
  cuisine_benchmarks: Array<{
    cuisine: string;
    avg_rating: number;
    avg_revenue: number;
    avg_orders: number;
    restaurant_count: number;
  }>;
  performance_matrix: Array<{
    restaurant_id: string;
    name: string;
    city: string;
    cuisine: string;
    orders: number;
    revenue: number;
    health_score: number;
    rating: number;
  }>;
  early_warnings: Array<{
    restaurant_id: string;
    restaurant_name: string;
    signal: string;
    severity: string;
    metric: string;
    action: string;
  }>;
  restaurant_ranking?: Array<{
    restaurant_id: string;
    name: string;
    city: string;
    cuisine: string;
    orders: number;
    revenue: number;
    revenue_share_pct: number;
    rating: number | null;
    health_score: number;
    avg_prep_duration_mins: number;
    cancellation_rate_pct: number;
  }>;
  underperforming_restaurants?: Array<{
    restaurant_id: string;
    name: string;
    city: string;
    cuisine: string;
    health_score: number;
    rating: number | null;
    orders: number;
    revenue: number;
    issue: string;
    recommended_action: string;
  }>;
  active_filters?: Record<string, any>;
}

export interface OperationsData {
  kpis: {
    total_deliveries: number;
    avg_duration_mins: number;
    ontime_rate_pct: number;
    active_riders: number;
    avg_distance_km: number;
    anomalies_detected: number;
  };
  screening_caveat?: string;
  delivery_vitals?: {
    total_deliveries: number;
    completed_deliveries: number;
    avg_duration_mins: number;
    late_delivery_pct: number;
    fleet_utilization_pct: number;
    telematics_mode: string;
  };
  rider_rankings?: Array<{
    rider_id: string;
    name: string;
    city: string;
    vehicle_type: string;
    completed_deliveries: number;
    avg_duration_mins: number;
    avg_distance_km: number;
    experience_years: number;
  }>;
  city_operations?: Array<{
    city: string;
    deliveries: number;
    avg_duration_mins: number;
    late_deliveries: number;
    late_delivery_pct: number;
  }>;
  demand_forecast: Array<{
    date: string;
    actual: number | null;
    forecast: number | null;
    upper: number | null;
    lower: number | null;
    has_actual?: boolean;
    missing_actual_reason?: string | null;
  }>;
  demand_heatmap: Array<{
    city: string;
    time_slot: string;
    demand_density: number;
    total_orders?: number;
    trend_pct?: number;
    demand_status?: string | null;
    cancellation_rate_pct?: number;
  }>;
  rider_allocation: Array<{
    city: string;
    current_riders: number;
    recommended_riders: number | null;
    deficit: number | null;
    assigned_dispatch_orders?: number;
    unique_dispatched_riders?: number;
    avg_allocation_score?: number | null;
    urgency: string;
  }>;
  anomalies: Array<{
    id: string;
    entity_type?: string;
    type: string;
    severity: string;
    description: string;
    impact: string;
    is_confirmed_incident?: boolean;
  }>;
  active_filters?: Record<string, any>;
}

export interface FinancialData {
  kpis: {
    gross_merchandise_value: number;
    commission_revenue: number;
    delivery_fee_revenue: number;
    discount_subsidies: number;
    net_platform_revenue: number;
    realized_operating_profit?: number;
    profit_margin_pct: number;
    take_rate_pct?: number;
    total_potential_risk_exposure?: number;
    total_revenue_leakage: number;
    leakage_confirmed?: boolean;
  };
  unit_economics: {
    aov: number;
    gross_aov?: number;
    commission_take_rate: number;
    avg_delivery_fee: number;
    avg_discount_subsidy: number;
    net_unit_contribution: number;
  };
  revenue_trends?: {
    daily: Array<{ date: string; gmv: number; net_revenue: number; orders: number }>;
    weekly: Array<{ week: string; gmv: number; net_revenue: number; orders: number }>;
    monthly: Array<{ month: string; gmv: number; net_revenue: number; orders: number }>;
  };
  payment_methods?: Array<{
    payment_method: string;
    order_count: number;
    gmv: number;
    percentage: number;
  }>;
  city_financials?: Array<{
    city: string;
    gmv: number;
    net_revenue: number;
    orders: number;
    estimated_commission: number;
    take_rate_pct: number;
  }>;
  aov_trend?: Array<{
    month: string;
    net_aov: number;
    gross_aov: number;
  }>;
  revenue_leakage: Array<{
    category: string;
    amount: number;
    flagged_order_count?: number;
    severity: string;
    impacted_metric: string;
    detection_category?: string;
    is_confirmed_loss?: boolean;
    classification?: string;
    recommended_action: string;
  }>;
  promotions: Array<{
    promo_id?: string;
    promo_name?: string;
    promo_type?: string;
    code: string;
    discount_pct: number | null;
    campaign_budget?: number | null;
    redemptions: number | null;
    gmv_driven: number | null;
    roi_multiple: number | null;
    attribution_status?: string;
  }>;
  active_filters?: Record<string, any>;
}

export interface DecisionAction {
  id: string;
  domain: string;
  title: string;
  severity: string;
  target: string;
  evidence: string;
  reason: string;
  confidence_pct: number | null;
  confidence_status?: string;
  model_readiness?: string;
  model_evaluation_metric?: string;
}

export interface SimulationParams {
  commission_change_pct: number;
  delivery_fee_change_pct: number;
  discount_change_pct: number;
  demand_change_pct: number;
  churn_reduction_pct: number;
  aov_change_pct: number;
}

export interface DigitalTwinState {
  status?: string;
  vitality_index: number | null;
  pillars: {
    customer_twin: {
      active_base: number | null;
      churn_exposure: number | null;
      clv_capital: number | null;
      engagement_index: number | null;
      Data_Status?: string;
    };
    restaurant_twin: {
      active_merchants: number | null;
      critical_partners: number | null;
      network_health: number | null;
      cancellation_rate: number | null;
      Data_Status?: string;
    };
    operations_twin: {
      active_fleet: number | null;
      avg_eta_mins: number | null;
      dispatch_fulfillment: number | null;
      bottlenecks: number | null;
      Data_Status?: string;
    };
    financial_twin: {
      gross_volume: number | null;
      net_platform_revenue: number | null;
      margin_rate: number | null;
      leakage_exposure: number | null;
      Data_Status?: string;
    };
  };
  systemic_alerts: any[];
  impact_ripple_chains: any[];
}

export interface VerifiedMetric {
  label: string;
  value: string | number;
  provenance?: string;
  delta?: string;
  status?: string;
  // Phase 14 Executive AI Copilot fields
  copilot_mode?: string;
  summary_data?: ExecutiveSummaryPayload;
  alerts?: BusinessAlert[];
  epistemic_classification?: {
    verified_facts_count?: number;
    model_predictions_count?: number;
    strategic_interpretations_count?: number;
    simulated_projections_count?: number;
  };
}

export interface ExecutiveSummaryPayload {
  summary_type: string;
  title: string;
  reporting_period: string;
  active_scope: string;
  verified_historical_facts: string[];
  model_predictions: Array<{ metric: string; value: string; confidence: string; model: string }>;
  strategic_interpretations: string[];
  simulated_projections: Array<{ scenario: string; projected_benefit: string; is_simulation_projection: boolean }>;
  epistemic_notice: string;
}

export interface RootCausePayload {
  target_kpi: string;
  baseline_metrics: Record<string, any>;
  contributing_factors: Array<{ factor: string; contribution_weight: string; evidence: string }>;
  dimensional_breakdown?: any[];
  correlation_vs_causation: string;
  uncertainty_and_limitations: string;
  recommended_investigative_actions: string[];
}

export interface BusinessAlert {
  alert_id: string;
  severity: string;
  business_area: string;
  title: string;
  summary: string;
  detection_time: string;
  supporting_evidence: string;
  confidence_level: string;
  is_statistical_screening: boolean;
  is_confirmed_loss: boolean;
  suggested_investigation: string;
  recommended_action: string;
}

export interface CopilotResponse extends ChatResponse {}

export interface SuggestedChart {
  type: 'bar' | 'line' | 'pie';
  title: string;
  x_key: string;
  y_key: string;
  series_name?: string;
  data: any[];
}

export interface SqlDetails {
  query: string;
  valid: boolean;
  validation_message: string;
}

export interface ContributingFactor {
  factor: string;
  correlation: string;
  evidence: string;
}

export interface RootCauseAnalysis {
  investigation_target: string;
  observed_facts: string[];
  contributing_factors: ContributingFactor[];
  uncertainties: string[];
  recommended_actions: string[];
}

export interface SimulationResultPayload {
  scenario_name: string;
  parameters: Record<string, number>;
  financial_impact: {
    baseline_revenue: number;
    simulated_revenue: number;
    revenue_diff: number;
    margin_diff_pct: number;
  };
  customer_impact: Record<string, any>;
  operations_impact: Record<string, any>;
  recommendation: {
    Decision: string;
    Expected_Benefit: string;
    Main_Risk: string;
  };
  comparison_data: Array<{ metric: string; Baseline: number; Simulated: number }>;
  summary: string;
}

export interface AIRecommendation {
  title: string;
  evidence: string;
  expected_impact: string;
  confidence: string;
  action: string;
}

export interface ProvenanceDetails {
  data_source: string;
  source_file?: string;
  records_loaded?: number;
  database?: string;
  last_updated?: string;
  access_mode?: string;
}

export interface StatusHistoryEntry {
  status: string;
  actor: string;
  timestamp: string;
  reason_or_notes?: string;
}

export interface RealizedOutcomeRecord {
  measured_by: string;
  measured_at: string;
  realized_gross_benefit_rupees: number;
  actual_cost_rupees: number;
  realized_net_financial_impact_rupees: number;
  variance_vs_projected_pct: number;
  audit_notes: string;
}

export interface PrescriptiveRecommendation {
  recommendation_id: string;
  title?: string;
  domain: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string;
  problem_statement: string;
  business_problem?: string;
  supporting_evidence: string[];
  evidence?: string;
  proposed_action: string;
  action?: string;
  expected_gross_benefit_rupees: number;
  implementation_cost_rupees: number;
  net_financial_impact_rupees: number;
  roi_multiple: number;
  payback_period_days: number;
  confidence_tier: 'HIGH' | 'MODERATE' | 'LOW_EMPIRICAL' | 'OPERATIONAL_GATED' | string;
  status: 'Proposed' | 'Under Review' | 'Approved' | 'Rejected' | 'In Progress' | 'Implemented' | 'Outcome Recorded' | string;
  status_history: StatusHistoryEntry[];
  approved_by?: string | null;
  approval_notes?: string | null;
  rejected_by?: string | null;
  rejection_reason?: string | null;
  outcome_record?: RealizedOutcomeRecord | null;
  requires_human_approval: boolean;
  metadata?: Record<string, any>;
}

export interface PrescriptiveSummary {
  total_recommendations: number;
  total_gross_benefit_rupees: number;
  total_implementation_cost_rupees: number;
  total_net_financial_impact_rupees: number;
  overall_roi_multiple: number;
  by_domain_counts: Record<string, number>;
  by_confidence_tier_counts: Record<string, number>;
  by_status_counts: Record<string, number>;
}

export interface ControlledSimulationResult {
  scenario_type: string;
  scenario_title: string;
  is_simulation_projection: boolean;
  disclaimer: string;
  baseline: {
    delivered_orders: number;
    realized_gross_gmv: number;
    realized_net_revenue: number;
    realized_average_order_value: number;
    net_contribution_margin: number;
    margin_percentage: number;
    sla_breach_count: number;
    sla_breach_rate_pct: number;
  };
  scenario_assumptions: string[];
  projected_outcomes: {
    projected_delivered_orders: number;
    projected_gross_gmv: number;
    projected_net_revenue: number;
    projected_contribution_margin: number;
    projected_margin_percentage: number;
    projected_sla_breaches: number;
    projected_sla_breach_rate_pct: number;
  };
  variance_deltas: {
    orders_delta: number;
    gmv_delta: number;
    net_revenue_delta: number;
    margin_delta_rupees: number;
    margin_delta_percentage: number;
    sla_breaches_prevented: number;
  };
}

export interface CustomerPrescriptiveProfile {
  customer_id: string;
  persona: string;
  city: string;
  retention_segment: string;
  behavioral_telemetry: {
    days_since_last_order: number;
    total_lifetime_orders: number;
    lifetime_spend: number;
    average_order_value: number;
  };
  ml_caveat_assessment: {
    raw_churn_ml_probability: number | null;
    ml_confidence_tier: string;
    confidence_caveat: string;
  };
  discount_guardrails: {
    eligible_for_subsidy: boolean;
    max_discount_percentage: number;
    minimum_order_value_required: number;
    capped_subsidy_budget: number;
    projected_contribution_margin: number;
  };
  prescriptive_action: string;
}

export interface RestaurantPrescriptiveProfile {
  restaurant_id: string;
  restaurant_name: string;
  city: string;
  diagnosis_category: string;
  operational_metrics: {
    total_orders_fulfilled: number;
    cancellation_rate_percentage: number;
    customer_rating: number;
    average_prep_time_minutes: number;
    active_menu_items: number;
  };
  prescriptive_action_plan: string[];
  expected_operational_impact: string;
}

export interface RiderFleetWorkload {
  status: string;
  total_active_fleet: number;
  total_dispatches: number;
  fleet_sla_metrics: {
    average_delivery_duration_minutes: number;
    sla_breached_deliveries_gt_45m: number;
    sla_breach_rate_percentage: number;
    long_distance_deliveries_gt_7km: number;
    long_distance_percentage: number;
  };
  geographic_workload: Record<
    string,
    {
      registered_riders: number;
      total_deliveries: number;
      orders_per_rider_ratio: number;
      status: string;
    }
  >;
  fleet_composition_by_vehicle: Record<string, number>;
  live_telemetry_disclaimer: string;
}

export interface PrescriptiveFinancialCharts {
  contribution_margin_waterfall: Array<{
    name: string;
    amount: number;
    type: 'total' | 'positive' | 'negative' | 'subtotal';
  }>;
  revenue_vs_cost_comparison: Array<{
    category: string;
    amount: number;
  }>;
  summary: {
    status: string;
    delivered_order_count: number;
    realized_gross_gmv: number;
    realized_net_revenue: number;
    realized_average_order_value: number;
    financial_breakdown: {
      gross_food_gmv: number;
      estimated_platform_commission_20pct: number;
      total_delivery_fees_collected: number;
      average_delivery_fee_collected: number;
      total_discounts_applied: number;
      platform_subsidized_discount_share_60pct: number;
      estimated_rider_fulfillment_cost: number;
      net_platform_contribution_margin: number;
      contribution_margin_percentage: number;
    };
    revenue_leakage_diagnosis: {
      heavy_discount_orders_count: number;
      heavy_discount_orders_pct: number;
      heavy_discount_total_value: number;
      small_basket_orders_count: number;
      small_basket_orders_pct: number;
      small_basket_total_gmv: number;
    };
  };
}

export interface InvokedAgentSummary {
  agent_id: string;
  domain: string;
  status: string;
  elapsed_ms: number;
  stage: number;
  data_sources: string[];
}

export interface TelemetryEvent {
  request_id: string;
  session_id: string;
  event_type:
    | 'query_received'
    | 'intent_classified'
    | 'agent_started'
    | 'agent_progress'
    | 'agent_completed'
    | 'agent_failed'
    | 'synthesis_started'
    | 'verification_completed'
    | 'response_completed'
    | 'execution_failed'
    | 'heartbeat'
    | string;
  timestamp: number;
  agent_name?: string | null;
  status: string;
  duration_ms?: number | null;
  message: string;
  stage?: number | null;
  data?: any;
}

export interface CalculationStep {
  kpi_id?: string;
  name: string;
  value: number | string;
  unit?: string;
  formula: string;
  source_tables?: string;
}

export interface AiAgentsStatusResponse {
  status: string;
  orchestrator_version: string;
  principal_role: string;
  active_contexts: number;
  data_store: {
    source: string;
    datasets_loaded: number;
  };
  registered_agents: Array<{
    agent_id: string;
    domain: string;
    version: string;
    availability: string;
    is_implemented: boolean;
    capabilities: string[];
    supported_intents: string[];
    allowed_tables: string[];
    required_scopes: string[];
    timeout_seconds: number;
  }>;
  experimental_ml_models: Array<{
    model: string;
    validation_status: string;
    is_production_ready: boolean;
  }>;
}

export interface ChatResponse {
  question: string;
  resolved_query?: string | null;
  intent?: string;
  route: string;
  answer: string;
  provider_status: 'ready' | 'unconfigured' | 'mock' | 'error' | string;
  verified_metrics?: VerifiedMetric[];
  suggested_chart?: SuggestedChart | null;
  sql?: SqlDetails | null;
  sql_query: string;
  sql_valid: boolean;
  validation_message: string;
  data_rows: any[];
  root_cause_analysis?: RootCauseAnalysis | null;
  simulation_results?: SimulationResultPayload | null;
  recommendations?: AIRecommendation[];
  follow_up_suggestions?: string[];
  provenance?: ProvenanceDetails;
  insights: string[];
  timestamp: string;
  // Phase 06.3 Multi-Agent Observability Fields
  request_id?: string;
  trace_id?: string;
  orchestration_mode?: 'single_agent' | 'multi_agent' | 'sql_sandbox' | 'general_assistant' | string;
  agents_invoked?: InvokedAgentSummary[];
  consolidated_summary?: string;
  calculation_steps?: CalculationStep[];
  ml_confidence_warnings?: string[];
  limitations?: string[];
  data_source_badges?: string[];
  grounding_verified?: boolean;
  verification_outcome?: 'verified' | 'partial' | 'rejected' | 'not_run' | string;
  status?: string;
  // Phase 14 Executive AI Copilot fields
  copilot_mode?: string;
  summary_data?: ExecutiveSummaryPayload;
  alerts?: BusinessAlert[];
  epistemic_classification?: {
    verified_facts_count?: number;
    model_predictions_count?: number;
    strategic_interpretations_count?: number;
    simulated_projections_count?: number;
  };
}

export interface ExecutiveSummaryPayload {
  summary_type: string;
  title: string;
  reporting_period: string;
  active_scope: string;
  verified_historical_facts: string[];
  model_predictions: Array<{ metric: string; value: string; confidence: string; model: string }>;
  strategic_interpretations: string[];
  simulated_projections: Array<{ scenario: string; projected_benefit: string; is_simulation_projection: boolean }>;
  epistemic_notice: string;
}

export interface RootCausePayload {
  target_kpi: string;
  baseline_metrics: Record<string, any>;
  contributing_factors: Array<{ factor: string; contribution_weight: string; evidence: string }>;
  dimensional_breakdown?: any[];
  correlation_vs_causation: string;
  uncertainty_and_limitations: string;
  recommended_investigative_actions: string[];
}

export interface BusinessAlert {
  alert_id: string;
  severity: string;
  business_area: string;
  title: string;
  summary: string;
  detection_time: string;
  supporting_evidence: string;
  confidence_level: string;
  is_statistical_screening: boolean;
  is_confirmed_loss: boolean;
  suggested_investigation: string;
  recommended_action: string;
}

export interface CopilotResponse extends ChatResponse {}

export interface FetchJsonOptions extends RequestInit {
  timeoutMs?: number;
  maxRetries?: number;
}

const DEFAULT_TIMEOUT_MS = 20000;
const AI_ASK_TIMEOUT_MS = 68000;
const RETRYABLE_HTTP_STATUSES = new Set([502, 503, 504]);

function delayMs(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchJson<T>(url: string, options?: FetchJsonOptions): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, maxRetries, ...fetchOptions } = options || {};
  const method = (fetchOptions.method || "GET").toUpperCase();
  // STRICT RULE: Only retry safe idempotent read requests (never POST/PUT/DELETE mutations)
  const isSafeIdempotent = method === "GET" || method === "HEAD";
  const attemptsAllowed = 1 + (isSafeIdempotent ? Math.max(0, Math.min(maxRetries ?? 1, 2)) : 0);

  let lastError: unknown;
  for (let attempt = 0; attempt < attemptsAllowed; attempt++) {
    const token = getApiToken();
    const headers = new Headers(fetchOptions.headers || {});
    if (token) {
      if (!headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
      }
      if (!headers.has("X-API-Key")) {
        headers.set("X-API-Key", token);
      }
    }
    // Distributed tracing headers (W3C traceparent + correlation IDs)
    if (!headers.has("x-request-id")) {
      const randId = Math.random().toString(36).substring(2, 12);
      headers.set("x-request-id", `req_${randId}`);
    }

    const controller = new AbortController();
    const externalSignal = fetchOptions.signal;
    const onExternalAbort = () => controller.abort();
    if (externalSignal) {
      if (externalSignal.aborted) {
        controller.abort();
      } else {
        externalSignal.addEventListener("abort", onExternalAbort, { once: true });
      }
    }
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      if (!res.ok) {
        let detail = "";
        try {
          const errBody = await res.json();
          if (errBody && typeof errBody.detail === "string") {
            detail = errBody.detail;
          }
        } catch {
          // Response may not be JSON
        }
        const msg = detail
          ? `API Error (${res.status}): ${detail}`
          : `API Error: ${res.status} ${res.statusText}`;
        const apiErr = new ApiError(res.status, msg, detail);
        if (isSafeIdempotent && RETRYABLE_HTTP_STATUSES.has(res.status) && attempt < attemptsAllowed - 1) {
          lastError = apiErr;
          await delayMs(250 * Math.pow(2, attempt));
          continue;
        }
        throw apiErr;
      }
      return await res.json();
    } catch (err: any) {
      if (err instanceof ApiError) {
        throw err;
      }
      const isTimeout = err?.name === "AbortError";
      const wrapped = new ApiError(
        isTimeout ? 408 : 0,
        isTimeout
          ? `Request timed out after ${Math.round(timeoutMs / 1000)}s.`
          : err?.message || "Network error communicating with NovaNest API.",
      );
      lastError = wrapped;
      if (isSafeIdempotent && !externalSignal?.aborted && attempt < attemptsAllowed - 1) {
        await delayMs(250 * Math.pow(2, attempt));
        continue;
      }
      throw wrapped;
    } finally {
      window.clearTimeout(timer);
      if (externalSignal) {
        externalSignal.removeEventListener("abort", onExternalAbort);
      }
    }
  }

  throw lastError instanceof Error ? lastError : new ApiError(0, "Request failed after bounded retries.");
}

/**
 * Normalizes raw recommendation payloads from FastAPI into strictly typed, null-safe PrescriptiveRecommendation objects.
 * Guarantees supporting_evidence is always an array of strings, eliminating undefined .slice() and .map() exceptions.
 */
export function normalizePrescriptiveRecommendation(raw: any): PrescriptiveRecommendation {
  if (!raw || typeof raw !== 'object') {
    return {
      recommendation_id: 'UNKNOWN',
      domain: 'cross_domain',
      priority: 'MEDIUM',
      problem_statement: 'No problem statement available',
      supporting_evidence: [],
      proposed_action: 'No action specified',
      expected_gross_benefit_rupees: 0,
      implementation_cost_rupees: 0,
      net_financial_impact_rupees: 0,
      roi_multiple: 0,
      payback_period_days: 30,
      confidence_tier: 'MODERATE',
      status: 'Proposed',
      status_history: [],
      requires_human_approval: true,
    };
  }

  // Parse supporting_evidence cleanly: if string, split by '; ' or '\n'; if array, use it; else empty array
  let evidenceList: string[] = [];
  if (Array.isArray(raw.supporting_evidence)) {
    evidenceList = raw.supporting_evidence.filter((e: any) => typeof e === 'string' && e.trim().length > 0);
  } else if (typeof raw.evidence === 'string' && raw.evidence.trim().length > 0) {
    evidenceList = raw.evidence
      .split(';')
      .map((s: string) => s.trim())
      .filter((s: string) => s.length > 0);
  }

  const problem = raw.problem_statement || raw.business_problem || raw.title || 'Actionable Business Optimization';
  const action = raw.proposed_action || raw.action || '';
  const netImpact = Number(
    raw.net_financial_impact_rupees ??
    raw.net_financial_impact ??
    raw.financial_impact?.net_financial_impact ??
    0
  );
  const implCost = Number(
    raw.implementation_cost_rupees ??
    raw.implementation_cost ??
    raw.financial_impact?.implementation_cost ??
    0
  );
  const grossBenefit = Number(
    raw.expected_gross_benefit_rupees ??
    raw.financial_impact?.gross_benefit ??
    raw.expected_benefit ??
    (netImpact + implCost)
  );
  const roi = Number(
    raw.roi_multiple ??
    raw.financial_impact?.roi_multiple ??
    (implCost > 0 ? netImpact / implCost : 0)
  );
  const payback = Number(
    raw.payback_period_days ??
    raw.financial_impact?.payback_period_days ??
    30
  );

  const history = Array.isArray(raw.status_history)
    ? raw.status_history
    : [
        {
          status: raw.status || raw.lifecycle_status || 'Proposed',
          changed_at: new Date().toISOString(),
          changed_by: raw.approved_by || 'System Engine',
          notes: 'Initial state',
        },
      ];

  return {
    recommendation_id: String(raw.recommendation_id || 'REC-UNKNOWN'),
    domain: String(raw.domain || 'cross_domain'),
    priority: (raw.priority || 'MEDIUM').toUpperCase(),
    problem_statement: problem,
    supporting_evidence: evidenceList,
    proposed_action: action,
    expected_gross_benefit_rupees: grossBenefit,
    implementation_cost_rupees: implCost,
    net_financial_impact_rupees: netImpact,
    roi_multiple: roi,
    payback_period_days: payback,
    confidence_tier: String(raw.confidence_tier || 'MODERATE'),
    status: String(raw.status || raw.lifecycle_status || 'Proposed'),
    status_history: history,
    approved_by: raw.approved_by || null,
    approval_notes: raw.approval_notes || null,
    rejected_by: raw.rejected_by || null,
    rejection_reason: raw.rejection_reason || null,
    outcome_record: raw.outcome_record || raw.realized_outcome || null,
    requires_human_approval: raw.requires_human_approval ?? raw.human_approval_required ?? true,
    metadata: raw.metadata || {},
  };
}

/**
 * Normalizes PrescriptiveFinancialCharts payloads from FastAPI, ensuring all arrays are populated.
 */
export function normalizePrescriptiveFinancialCharts(raw: any): PrescriptiveFinancialCharts {
  if (!raw || typeof raw !== 'object') {
    return {
      contribution_margin_waterfall: [],
      revenue_vs_cost_comparison: [],
      summary: {
        status: 'nominal',
        delivered_order_count: 0,
        realized_gross_gmv: 0,
        realized_net_revenue: 0,
        realized_average_order_value: 0,
        financial_breakdown: {
          gross_food_gmv: 0,
          estimated_platform_commission_20pct: 0,
          total_delivery_fees_collected: 0,
          average_delivery_fee_collected: 0,
          total_discounts_applied: 0,
          platform_subsidized_discount_share_60pct: 0,
          estimated_rider_fulfillment_cost: 0,
          net_platform_contribution_margin: 0,
          contribution_margin_percentage: 0,
        },
        revenue_leakage_diagnosis: {
          heavy_discount_orders_count: 0,
          heavy_discount_orders_pct: 0,
          heavy_discount_total_value: 0,
          small_basket_orders_count: 0,
          small_basket_orders_pct: 0,
          small_basket_total_gmv: 0,
        },
      },
    };
  }

  return {
    contribution_margin_waterfall: Array.isArray(raw.contribution_margin_waterfall)
      ? raw.contribution_margin_waterfall
      : [],
    revenue_vs_cost_comparison: Array.isArray(raw.revenue_vs_cost_comparison)
      ? raw.revenue_vs_cost_comparison
      : [],
    summary: raw.summary || {
      status: 'nominal',
      delivered_order_count: 0,
      realized_gross_gmv: 0,
      realized_net_revenue: 0,
      realized_average_order_value: 0,
      financial_breakdown: {},
      revenue_leakage_diagnosis: {},
    },
  };
}

export const api = {
  getHealth: () => fetchJson<{ status: string; data_source: string; datasets: Record<string, number> }>(`${API_BASE}/health`),
  getOverview: (filters?: GlobalFilterParams | string) =>
    fetchJson<OverviewData>(`${API_BASE}/overview${buildQueryString(filters)}`),
  getCustomerOverview: (filters?: GlobalFilterParams) =>
    fetchJson<CustomerData>(`${API_BASE}/customer/overview${buildQueryString(filters)}`),
  getCustomerList: () => fetchJson<CustomerListItem[]>(`${API_BASE}/customer/list`),
  getCustomer360: (id: string) => fetchJson<Customer360Data>(`${API_BASE}/customer/360/${encodeURIComponent(id)}`),
  getRestaurantOverview: (filters?: GlobalFilterParams) =>
    fetchJson<RestaurantData>(`${API_BASE}/restaurant/overview${buildQueryString(filters)}`),
  getOperationsOverview: (filters?: GlobalFilterParams) =>
    fetchJson<OperationsData>(`${API_BASE}/operations/overview${buildQueryString(filters)}`),
  getFinancialOverview: (filters?: GlobalFilterParams) =>
    fetchJson<FinancialData>(`${API_BASE}/financial/overview${buildQueryString(filters)}`),
  getDecisionActions: () => fetchJson<DecisionAction[]>(`${API_BASE}/decision/actions`),
  getDigitalTwinState: () => fetchJson<DigitalTwinState>(`${API_BASE}/digital-twin/state`),
  simulateScenario: (params: SimulationParams) =>
    fetchJson<any>(`${API_BASE}/decision/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),
  askAi: (question: string, session_id?: string, city_filter?: string, contextual_data?: Record<string, any>) =>
    fetchJson<ChatResponse>(`${API_BASE}/ai/ask`, {
      method: "POST",
      timeoutMs: AI_ASK_TIMEOUT_MS,
      maxRetries: 0,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        session_id: session_id || "default",
        ...(city_filter ? { city_filter } : {}),
        ...(contextual_data ? { contextual_data } : {}),
      }),
    }),
  getStreamTicket: (sessionId: string = "default") =>
    fetchJson<{ ticket: string; expires_in: number; session_id: string; created_at: number }>(
      `${API_BASE}/ai/stream-ticket`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId || "default" }),
      }
    ),
  createEventSource: async (
    question: string,
    sessionId: string = "default",
    cityFilter?: string
  ): Promise<EventSource> => {
    const { ticket } = await api.getStreamTicket(sessionId);
    const params = new URLSearchParams({
      question,
      session_id: sessionId,
      ticket,
    });
    if (cityFilter && cityFilter !== "All") {
      params.append("city_filter", cityFilter);
    }
    return new EventSource(`${API_BASE}/ai/ask/stream?${params.toString()}`);
  },
  askAiStream: async (
    question: string,
    session_id?: string,
    city_filter?: string,
    onEvent?: (event: TelemetryEvent) => void,
    signal?: AbortSignal,
    contextual_data?: Record<string, any>
  ): Promise<ChatResponse> => {
    const cleanSession = session_id || "default";
    const token = getApiToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
      headers["X-API-Key"] = token;
    }

    try {
      const response = await fetch(`${API_BASE}/ai/ask/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          question,
          session_id: cleanSession,
          ...(city_filter ? { city_filter } : {}),
          ...(contextual_data ? { contextual_data } : {}),
        }),
        signal,
      });

      if (!response.ok || !response.body) {
        return await api.askAi(question, cleanSession, city_filter, contextual_data);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let finalChatResponse: ChatResponse | null = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          if (!block.trim()) continue;
          let dataStr = "";
          const fieldLines = block.split("\n");
          for (const line of fieldLines) {
            if (line.startsWith("data:")) {
              dataStr = line.slice(5).trim();
            }
          }

          if (dataStr) {
            try {
              const parsed: TelemetryEvent = JSON.parse(dataStr);
              if (onEvent) {
                onEvent(parsed);
              }
              if (parsed.event_type === "response_completed" && parsed.data) {
                finalChatResponse = parsed.data as ChatResponse;
              }
            } catch {
              // Ignore partial or unparseable SSE frame
            }
          }
        }
      }

      if (finalChatResponse) {
        return finalChatResponse;
      }

      return await api.askAi(question, cleanSession, city_filter, contextual_data);
    } catch (err: any) {
      if (err?.name === "AbortError") {
        throw err;
      }
      return await api.askAi(question, cleanSession, city_filter, contextual_data);
    }
  },
  getAiAgentsStatus: () => fetchJson<AiAgentsStatusResponse>(`${API_BASE}/ai/agents/status`),
  resetAiSession: (session_id: string) =>
    fetchJson<{ status: string; session_id: string; message: string }>(`${API_BASE}/ai/reset`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id }),
    }),

  // ============================================================
  // PRESCRIPTIVE DECISION INTELLIGENCE & ACTION CENTER (PHASE 09)
  // ============================================================
  getPrescriptiveRecommendations: async (params?: {
    domain?: string;
    status?: string;
    priority?: string;
    confidence?: string;
  }): Promise<PrescriptiveRecommendation[]> => {
    const q = new URLSearchParams();
    if (params?.domain) q.append("domain", params.domain);
    if (params?.status) q.append("status", params.status);
    if (params?.priority) q.append("priority", params.priority);
    if (params?.confidence) q.append("confidence", params.confidence);
    const qs = q.toString() ? `?${q.toString()}` : "";
    const raw = await fetchJson<any[]>(`${API_BASE}/prescriptive/recommendations${qs}`);
    if (!Array.isArray(raw)) return [];
    return raw.map(normalizePrescriptiveRecommendation);
  },

  getPrescriptiveSummary: () =>
    fetchJson<PrescriptiveSummary>(`${API_BASE}/prescriptive/summary`),

  getPrescriptiveRecommendation: async (recId: string): Promise<PrescriptiveRecommendation> => {
    const raw = await fetchJson<any>(`${API_BASE}/prescriptive/recommendations/${encodeURIComponent(recId)}`);
    return normalizePrescriptiveRecommendation(raw);
  },

  approvePrescriptiveRecommendation: async (recId: string, approved_by: string, approval_notes?: string) => {
    const res = await fetchJson<{ status: string; recommendation: any }>(
      `${API_BASE}/prescriptive/recommendations/${encodeURIComponent(recId)}/approve`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved_by, approval_notes }),
      }
    );
    return {
      status: res.status,
      recommendation: normalizePrescriptiveRecommendation(res.recommendation),
    };
  },

  rejectPrescriptiveRecommendation: async (recId: string, rejected_by: string, rejection_reason: string) => {
    const res = await fetchJson<{ status: string; recommendation: any }>(
      `${API_BASE}/prescriptive/recommendations/${encodeURIComponent(recId)}/reject`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rejected_by, rejection_reason }),
      }
    );
    return {
      status: res.status,
      recommendation: normalizePrescriptiveRecommendation(res.recommendation),
    };
  },

  startPrescriptiveProgress: async (recId: string, operator_user: string) => {
    const res = await fetchJson<{ status: string; recommendation: any }>(
      `${API_BASE}/prescriptive/recommendations/${encodeURIComponent(recId)}/start-progress`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operator_user }),
      }
    );
    return {
      status: res.status,
      recommendation: normalizePrescriptiveRecommendation(res.recommendation),
    };
  },

  markPrescriptiveImplemented: async (recId: string, operator_user: string) => {
    const res = await fetchJson<{ status: string; recommendation: any }>(
      `${API_BASE}/prescriptive/recommendations/${encodeURIComponent(recId)}/mark-implemented`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operator_user }),
      }
    );
    return {
      status: res.status,
      recommendation: normalizePrescriptiveRecommendation(res.recommendation),
    };
  },

  recordPrescriptiveOutcome: async (
    recId: string,
    outcome: {
      realized_gross_benefit: number;
      actual_cost: number;
      measured_by?: string;
      audit_notes?: string;
    }
  ) => {
    const res = await fetchJson<{ status: string; recommendation: any }>(
      `${API_BASE}/prescriptive/recommendations/${encodeURIComponent(recId)}/record-outcome`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(outcome),
      }
    );
    return {
      status: res.status,
      recommendation: normalizePrescriptiveRecommendation(res.recommendation),
    };
  },

  simulatePrescriptiveScenario: (scenario_type: string, overrides?: Record<string, any>) =>
    fetchJson<ControlledSimulationResult>(`${API_BASE}/prescriptive/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_type, overrides }),
    }),

  getPrescriptiveCustomerProfile: (customerId: string) =>
    fetchJson<CustomerPrescriptiveProfile>(
      `${API_BASE}/prescriptive/customer-profile/${encodeURIComponent(customerId)}`
    ),

  getPrescriptiveRestaurantProfile: (restaurantId: string) =>
    fetchJson<RestaurantPrescriptiveProfile>(
      `${API_BASE}/prescriptive/restaurant-profile/${encodeURIComponent(restaurantId)}`
    ),

  getPrescriptiveRiderFleetWorkload: () =>
    fetchJson<RiderFleetWorkload>(`${API_BASE}/prescriptive/rider-fleet-workload`),

  getPrescriptiveFinancialCharts: async (): Promise<PrescriptiveFinancialCharts> => {
    const raw = await fetchJson<any>(`${API_BASE}/prescriptive/financial-charts`);
    return normalizePrescriptiveFinancialCharts(raw);
  },

  // SRE Operations, Autonomic Health & Tracing
  getOperationsHealthLive: () =>
    fetchJson<{ status: string; uptime_seconds: number }>(`${API_BASE}/health/live`),
  getOperationsHealthReady: () =>
    fetchJson<{ status: string; checks: Record<string, any> }>(`${API_BASE}/health/ready`),
  getOperationsHealthDb: () =>
    fetchJson<{ status: string; connected: boolean; latency_ms: number }>(`${API_BASE}/health/db`),
  getOperationsHealthContainers: () =>
    fetchJson<{ status: string; total_containers: number; containers: Record<string, any> }>(`${API_BASE}/health/containers`),
  getOperationsTraces: (limit?: number) =>
    fetchJson<{ traces: any[] }>(`${API_BASE}/operations/traces${limit ? `?limit=${limit}` : ""}`),
  getOperationsAlerts: (limit?: number) =>
    fetchJson<{ alerts: any[] }>(`${API_BASE}/operations/alerts${limit ? `?limit=${limit}` : ""}`),
  triggerOperationsBackup: () =>
    fetchJson<any>(`${API_BASE}/operations/backup`, { method: "POST" }),
  triggerOperationsRestoreTest: () =>
    fetchJson<any>(`${API_BASE}/operations/restore-test`, { method: "POST" }),
  getOperationsPerformance: () =>
    fetchJson<any>(`${API_BASE}/operations/performance`),
  getOperationsDisasterRecovery: () =>
    fetchJson<any>(`${API_BASE}/operations/disaster-recovery`),

  // ============================================================
  // EXECUTIVE AI COPILOT & DECISION INTELLIGENCE (PHASE 14)
  // ============================================================
  queryCopilot: (
    question: string,
    session_id?: string,
    city_filter?: string,
    contextual_data?: Record<string, any>
  ) =>
    fetchJson<CopilotResponse>(`${API_BASE}/copilot/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, session_id, city_filter, contextual_data }),
    }),

  getCopilotSummaries: (summary_type: string = "monthly", city?: string) => {
    const q = new URLSearchParams();
    if (summary_type) q.append("summary_type", summary_type);
    if (city && city !== "All") q.append("city", city);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchJson<ExecutiveSummaryPayload>(`${API_BASE}/copilot/summaries${qs}`);
  },

  getCopilotRootCause: (target: string = "revenue_decline", city?: string) => {
    const q = new URLSearchParams();
    if (target) q.append("target", target);
    if (city && city !== "All") q.append("city", city);
    const qs = q.toString() ? `?${q.toString()}` : "";
    return fetchJson<RootCausePayload>(`${API_BASE}/copilot/root-cause${qs}`);
  },

  getCopilotAlerts: (city?: string) => {
    const qs = city && city !== "All" ? `?city=${encodeURIComponent(city)}` : "";
    return fetchJson<{ alerts: BusinessAlert[]; total_alerts: number }>(`${API_BASE}/copilot/alerts${qs}`);
  },

  simulateCopilotScenario: (scenario_type: string, overrides?: Record<string, any>) =>
    fetchJson<any>(`${API_BASE}/copilot/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_type, overrides }),
    }),

  getCopilotRecommendations: (domain?: string) => {
    const qs = domain && domain !== "All" ? `?domain=${encodeURIComponent(domain)}` : "";
    return fetchJson<PrescriptiveRecommendation[]>(`${API_BASE}/copilot/recommendations${qs}`);
  },
};
