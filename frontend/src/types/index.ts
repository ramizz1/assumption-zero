/** Core TypeScript types matching the backend Pydantic schemas */

export type EvidenceType =
  | 'competitor' | 'demand' | 'complaint' | 'pricing' | 'regulatory'
  | 'market_direction' | 'distribution' | 'failed_product' | 'geographic'
  | 'oss_alternative' | 'manual_workflow' | 'failure_reason' | 'general'

export type ReliabilityLevel = 'low' | 'medium' | 'high'
export type ConfidenceLevel = 'low' | 'medium' | 'high'
export type AnalysisStatus = 'pending' | 'running' | 'complete' | 'failed'
export type Recommendation = 'Build' | 'Test First' | 'Pivot' | 'Avoid'
export type ResearchDepth = 'standard' | 'deep' | 'exhaustive'
export type PerspectiveName = 'market_analyst' | 'regional_strategist' | 'skeptical_investor' | 'customer_researcher' | 'practical_builder'
export type CompetitorType = 'direct' | 'indirect'

export type AnalysisStage =
  | 'clarifying_idea'
  | 'generating_queries'
  | 'collecting_evidence'
  | 'finding_competitors'
  | 'running_perspectives'
  | 'checking_citations'
  | 'calculating_scores'
  | 'generating_experiments'
  | 'complete'

export interface IdeaInput {
  name: string
  description: string
  problem: string
  target_customer: string
  geography: string
  market_language?: string
  currency?: string
  industry?: string
  startup_stage?: string
  solution?: string
  business_model?: string
  price?: string
  founder_skills?: string
  team?: string
  budget?: string
  launch_timeline?: string
  revenue_goal?: string
  acquisition_channels?: string
  known_competitors?: string
  unfair_advantage?: string
  key_assumptions?: string
  regulatory_constraints?: string
  additional_context?: string
}

export interface EvidenceItem {
  evidence_id: string
  title: string
  url: string
  evidence_origin: string
  source_name: string
  publication_date?: string
  retrieval_date: string
  passage: string
  search_query: string
  evidence_type: EvidenceType
  reliability: ReliabilityLevel
  relevance_score: number
  retrieval_timestamp: string
  is_demo: boolean
}

export interface Competitor {
  name: string
  url: string
  competitor_type: CompetitorType
  description: string
  target_user: string
  pricing_evidence?: string
  strengths: string[]
  weaknesses: string[]
  complaints: string[]
  differentiation: string[]
  evidence_ids: string[]
  confidence: ConfidenceLevel
}

export interface DimensionScore {
  dimension: string
  display_name: string
  raw_score: number
  weight: number
  weighted_score: number
  explanation: string
  supporting_evidence_ids: string[]
  contradicting_evidence_ids: string[]
  confidence: ConfidenceLevel
  missing_information: string[]
}

export interface OpportunityScore {
  total: number
  dimensions: DimensionScore[]
}

export interface AnalysisPerspective {
  perspective_name: PerspectiveName
  perspective_display: string
  model_id: string
  summary: string
  key_findings: string[]
  risks: string[]
  opportunities: string[]
  recommendation: Recommendation
  cited_evidence_ids: string[]
  invalid_citations: string[]
  dimension_scores: Record<string, number>
  most_dangerous_assumption: string
}

export interface DisagreementPosition {
  perspective: string
  model_id: string
  position: string
  evidence_ids: string[]
}

export interface ModelDisagreement {
  topic: string
  positions: DisagreementPosition[]
  stronger_position?: string
  requires_human_research: boolean
}

export interface ValidationExperiment {
  title: string
  assumption_tested: string
  why_it_matters: string
  procedure: string
  estimated_time: string
  estimated_cost_range: string
  success_threshold: string
  failure_threshold: string
  decision_after: string
  legal_ethical: string
  priority: number
}

export interface FounderAction {
  phase: string
  objective: string
  actions: string[]
  success_metric: string
  stop_condition: string
  budget_hint: string
}

export interface FounderToolkit {
  one_sentence_pitch: string
  ideal_customer_profile: string
  beachhead_market: string
  recommended_channels: string[]
  key_metrics: string[]
  roadmap: FounderAction[]
  interview_questions: string[]
  decision_rules: string[]
}

export interface RegionalEvidenceSignal {
  evidence_id: string
  category: string
  title: string
  source_name: string
  relevance_score: number
}

export interface RegionalMarketAnalysis {
  geography: string
  demand_score: number
  confidence: ConfidenceLevel
  evidence_count: number
  source_count: number
  summary: string
  demand_signals: RegionalEvidenceSignal[]
  pricing_signals: RegionalEvidenceSignal[]
  regulatory_signals: RegionalEvidenceSignal[]
  distribution_signals: RegionalEvidenceSignal[]
  localization_requirements: string[]
  research_gaps: string[]
}

export interface ResearchCoverage {
  depth: ResearchDepth
  queries_generated: number
  queries_executed: number
  providers_used: string[]
  evidence_collected: number
  regional_evidence_count: number
}

export interface AnalysisResult {
  analysis_id: string
  status: AnalysisStatus
  stage: AnalysisStage
  stage_description: string
  created_at: string
  completed_at?: string
  idea_input: IdeaInput
  interpreted_idea?: string
  evidence: EvidenceItem[]
  competitors: Competitor[]
  perspectives: AnalysisPerspective[]
  opportunity_score?: OpportunityScore
  evidence_confidence?: ConfidenceLevel
  recommendation?: Recommendation
  most_dangerous_assumption?: string
  strongest_supporting?: string
  strongest_contradicting?: string
  missing_information: string[]
  experiments: ValidationExperiment[]
  founder_toolkit?: FounderToolkit
  regional_analysis?: RegionalMarketAnalysis
  research_coverage?: ResearchCoverage
  disagreements: ModelDisagreement[]
  models_used: string[]
  provider_errors: string[]
  is_demo: boolean
  error_message?: string
}

export interface AnalysisListItem {
  analysis_id: string
  status: AnalysisStatus
  stage: AnalysisStage
  created_at: string
  completed_at?: string
  idea_name: string
  is_demo: boolean
  opportunity_score?: number
  recommendation?: Recommendation
}

export interface HealthResponse {
  status: string
  version: string
  ai_provider: string
  research_providers: string[]
  demo_mode: boolean
}
