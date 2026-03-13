/**
 * TypeScript types for Instalily Lead Management Dashboard
 */

export type LeadStatus = "Open" | "In Progress" | "Unqualified" | "Closed"
export type FitScoreLabel = "High" | "Medium" | "Low"

export interface Event {
  name: string
  date: string
  location: string
  relevance: string
  source_url?: string
}

export interface Company {
  name: string
  website: string
  revenue_estimate: string
  size: string
  description: string
  competitor_flag: boolean
  enrichment_status: string
}

export interface QualificationScores {
  industry_fit: number
  size_and_revenue: number
  strategic_relevance: number
  event_engagement: number
}

export interface Qualification {
  scores: QualificationScores
  weighted_total: number
  label: FitScoreLabel
  rationale: string
}

export interface DecisionMaker {
  name: string
  title: string
  linkedin: string | null
  source: string
  email: string | null
  phone: string | null
  clay_stub: string
  linkedin_stub: string
}

export interface Outreach {
  subject: string
  message: string
  status: string
}

export interface CRMData {
  lead_status: LeadStatus
  lead_owner: string
  last_interaction_date: string | null
  created_date: string
  notes: string
}

export interface Lead {
  event: Event
  company: Company
  qualification: Qualification
  decision_maker: DecisionMaker | null
  outreach: Outreach | null
  crm_data: CRMData
}

export interface LeadsData {
  generated_at: string
  pipeline_version: string
  leads: Lead[]
}

/**
 * Extended lead type with computed fields for the dashboard
 */
export interface LeadTableRow extends Lead {
  id: string // Computed unique ID
  industry: string // Computed from company description
}

/**
 * Filter state for the dashboard
 */
export interface FilterState {
  leadOwner: string
  leadStatus: LeadStatus | "All"
  fitScore: FitScoreLabel | "All"
}

/**
 * API request/response types
 */
export interface UpdateLeadRequest {
  id: string
  updates: Partial<CRMData>
}

export interface UpdateLeadResponse {
  success: boolean
  message?: string
  lead?: Lead
}

export interface GetLeadsResponse {
  success: boolean
  data?: LeadsData
  message?: string
}
