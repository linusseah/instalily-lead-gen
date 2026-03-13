"use client"

import { useState, useEffect, useRef } from "react"
import { X, Copy, ExternalLink, Check, ChevronDown, ChevronUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import type { LeadTableRow, LeadStatus } from "@/lib/types"
import {
  formatDate,
  getFitScoreColor,
  getLeadStatusColor,
  copyToClipboard,
  calculateScoreBreakdown,
} from "@/lib/utils"

interface LeadDetailPanelProps {
  lead: LeadTableRow | null
  isOpen: boolean
  onClose: () => void
  onUpdate: (id: string, updates: Partial<LeadTableRow["crm_data"]>) => Promise<void>
}

export function LeadDetailPanel({ lead, isOpen, onClose, onUpdate }: LeadDetailPanelProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null)
  const [showScoreBreakdown, setShowScoreBreakdown] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [hasAnimated, setHasAnimated] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)
  const [formData, setFormData] = useState({
    lead_status: "" as LeadStatus,
    lead_owner: "",
    last_interaction_date: "",
    notes: "",
  })

  // Initialize form data only when lead ID changes (switching leads) or panel opens
  // Do NOT update when lead object changes (prevents scroll jump on save)
  useEffect(() => {
    if (lead && isOpen) {
      setFormData({
        lead_status: lead.crm_data.lead_status,
        lead_owner: lead.crm_data.lead_owner,
        last_interaction_date: lead.crm_data.last_interaction_date || "",
        notes: lead.crm_data.notes,
      })
    }
  }, [lead?.id, isOpen]) // Only reset when lead ID changes or panel opens

  // Track when panel opens to show animation only once
  useEffect(() => {
    if (isOpen) {
      setHasAnimated(true)
    } else {
      setHasAnimated(false)
    }
  }, [isOpen])

  if (!isOpen || !lead) return null

  const handleCopy = async (text: string, field: string) => {
    const success = await copyToClipboard(text)
    if (success) {
      setCopiedField(field)
      setTimeout(() => setCopiedField(null), 2000)
    }
  }

  const handleSave = async () => {
    // Save current scroll position
    const scrollPosition = panelRef.current?.scrollTop || 0

    setIsSaving(true)

    // Clean form data - convert empty strings to null for optional fields
    const cleanedData = {
      ...formData,
      last_interaction_date: formData.last_interaction_date || null,
    }

    await onUpdate(lead.id, cleanedData)
    setIsSaving(false)

    // Restore scroll position after update
    requestAnimationFrame(() => {
      if (panelRef.current) {
        panelRef.current.scrollTop = scrollPosition
      }
    })
  }

  const scoreBreakdown = calculateScoreBreakdown(lead.qualification.scores)

  return (
    <>
      {/* Overlay */}
      <div
        className="slide-panel-overlay animate-in fade-in"
        onClick={onClose}
      />

      {/* Panel */}
      <div ref={panelRef} className={`slide-panel ${!hasAnimated ? 'animate-slide-in-right' : ''}`}>
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {lead.decision_maker?.name ?? "Unknown Lead"}
            </h2>
            <p className="text-sm text-gray-500">{lead.decision_maker?.title ?? "—"}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-6">
          {/* Contact Info */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Contact Information</h3>
            <div className="space-y-2">
              {lead.decision_maker?.email ? (
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-gray-500">Email</div>
                    <div className="text-sm text-gray-900">{lead.decision_maker.email}</div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopy(lead.decision_maker!.email!, "email")}
                  >
                    {copiedField === "email" ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              ) : (
                <div className="text-sm text-gray-500">
                  Email: {lead.decision_maker?.clay_stub || "Not available"}
                </div>
              )}

              {lead.decision_maker?.phone ? (
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-gray-500">Phone</div>
                    <div className="text-sm text-gray-900">{lead.decision_maker.phone}</div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopy(lead.decision_maker!.phone!, "phone")}
                  >
                    {copiedField === "phone" ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              ) : (
                <div className="text-sm text-gray-500">
                  Phone: {lead.decision_maker?.clay_stub || "Not available"}
                </div>
              )}

              {lead.decision_maker?.linkedin && (
                <div>
                  <div className="text-xs text-gray-500">LinkedIn</div>
                  <a
                    href={lead.decision_maker.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
                  >
                    View Profile <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          </section>

          {/* Company Info */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Company Information</h3>
            <div className="space-y-2">
              <div>
                <div className="text-xs text-gray-500">Company Name</div>
                <div className="text-sm text-gray-900 font-medium">
                  {lead.company.name}
                  {lead.company.competitor_flag && (
                    <Badge className="ml-2 bg-orange-100 text-orange-800 border-orange-200">
                      Competitor
                    </Badge>
                  )}
                </div>
              </div>
              {lead.company.website && (
                <div>
                  <div className="text-xs text-gray-500">Website</div>
                  <a
                    href={lead.company.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
                  >
                    {lead.company.website} <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
              <div>
                <div className="text-xs text-gray-500">Revenue</div>
                <div className="text-sm text-gray-900">{lead.company.revenue_estimate}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Size</div>
                <div className="text-sm text-gray-900">{lead.company.size}</div>
              </div>
              <div>
                <div className="text-xs text-gray-500">Description</div>
                <div className="text-sm text-gray-700 leading-relaxed">
                  {lead.company.description}
                </div>
              </div>
            </div>
          </section>

          {/* Fit Score Breakdown */}
          <section>
            <button
              onClick={() => setShowScoreBreakdown(!showScoreBreakdown)}
              className="flex items-center justify-between w-full text-sm font-semibold text-gray-900 mb-3 hover:text-gray-700"
            >
              <span>Qualification Score Breakdown</span>
              {showScoreBreakdown ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>

            {showScoreBreakdown && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">Overall Score</span>
                  <Badge className={getFitScoreColor(lead.qualification.label)}>
                    {lead.qualification.label} ({lead.qualification.weighted_total})
                  </Badge>
                </div>

                {Object.entries(scoreBreakdown).map(([key, data]) => (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-600 capitalize">
                        {key.replace(/_/g, " ")} ({data.weight}%)
                      </span>
                      <span className="text-xs font-medium text-gray-900">
                        {data.score}/10
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${data.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}

                <div className="bg-gray-50 p-3 rounded-md">
                  <div className="text-xs text-gray-500 mb-1">Rationale</div>
                  <div className="text-sm text-gray-700 leading-relaxed">
                    {lead.qualification.rationale}
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Industry Engagement */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Industry Engagement</h3>
            {lead.industry_engagement ? (
              <div className="space-y-2">
                <Badge
                  className={
                    lead.industry_engagement.confidence === "confirmed"
                      ? "bg-green-100 text-green-800 border-green-200"
                      : lead.industry_engagement.confidence === "historical"
                      ? "bg-blue-100 text-blue-800 border-blue-200"
                      : "bg-gray-100 text-gray-600 border-gray-200"
                  }
                >
                  {lead.industry_engagement.confidence === "confirmed"
                    ? "Confirmed"
                    : lead.industry_engagement.confidence === "historical"
                    ? "Historical"
                    : "Inferred"}
                </Badge>
                <div className="text-sm text-gray-700 leading-relaxed">
                  {lead.industry_engagement.summary}
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">Not available</div>
            )}
          </section>

          {/* Outreach Message */}
          {lead.outreach && (
            <section>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Recommended Outreach
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Subject</div>
                  <div className="text-sm text-gray-900 bg-gray-50 p-2 rounded">
                    {lead.outreach.subject}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Message</div>
                  <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded whitespace-pre-wrap leading-relaxed">
                    {lead.outreach.message}
                  </div>
                </div>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() =>
                    handleCopy(
                      `Subject: ${lead.outreach!.subject}\n\n${lead.outreach!.message}`,
                      "outreach"
                    )
                  }
                >
                  {copiedField === "outreach" ? (
                    <>
                      <Check className="w-4 h-4 mr-2" /> Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-2" /> Copy Outreach
                    </>
                  )}
                </Button>
              </div>
            </section>
          )}

          {/* CRM Fields */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">CRM Data</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-600 block mb-1">Lead Status</label>
                <Select
                  value={formData.lead_status}
                  onChange={(e) =>
                    setFormData({ ...formData, lead_status: e.target.value as LeadStatus })
                  }
                >
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Unqualified">Unqualified</option>
                  <option value="Closed">Closed</option>
                </Select>
              </div>

              <div>
                <label className="text-xs text-gray-600 block mb-1">Lead Owner</label>
                <Input
                  type="text"
                  value={formData.lead_owner}
                  onChange={(e) =>
                    setFormData({ ...formData, lead_owner: e.target.value })
                  }
                  placeholder="Enter lead owner name"
                />
              </div>

              <div>
                <label className="text-xs text-gray-600 block mb-1">
                  Last Interaction Date
                </label>
                <Input
                  type="date"
                  value={formData.last_interaction_date}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      last_interaction_date: e.target.value,
                    })
                  }
                />
              </div>

              <div>
                <label className="text-xs text-gray-600 block mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData({ ...formData, notes: e.target.value })
                  }
                  placeholder="Add notes about this lead..."
                  className="w-full min-h-[100px] px-3 py-2 text-sm border border-input rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>

              <Button
                onClick={handleSave}
                disabled={isSaving}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </section>
        </div>
      </div>
    </>
  )
}
