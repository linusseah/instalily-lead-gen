"use client"

import { useState, useEffect, useMemo } from "react"
import { TrendingUp, Users, Clock, Target, RefreshCw, Info } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { LeadTable } from "@/components/LeadTable"
import { LeadDetailPanel } from "@/components/LeadDetailPanel"
import type { LeadsData, LeadTableRow, FilterState, LeadStatus, FitScoreLabel } from "@/lib/types"
import { classifyIndustry, formatDate } from "@/lib/utils"

export default function DashboardPage() {
  const [leadsData, setLeadsData] = useState<LeadsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedLead, setSelectedLead] = useState<LeadTableRow | null>(null)
  const [isPanelOpen, setIsPanelOpen] = useState(false)
  const [showScoreInfo, setShowScoreInfo] = useState(false)

  const [filters, setFilters] = useState<FilterState>({
    leadOwner: "All",
    leadStatus: "All",
    fitScore: "All",
  })

  // Fetch leads data
  const fetchLeads = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch("/api/leads")
      const result = await response.json()

      if (!result.success) {
        throw new Error(result.message || "Failed to fetch leads")
      }

      setLeadsData(result.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLeads()
  }, [])

  // Transform leads into table rows with computed fields
  const tableRows: LeadTableRow[] = useMemo(() => {
    if (!leadsData) return []

    return leadsData.leads.map((lead) => ({
      ...lead,
      // Use the UUID from Supabase, not a generated compound ID
      id: lead.id,
      industry: classifyIndustry(lead.company.description),
    }))
  }, [leadsData])

  // Filter leads
  const filteredLeads = useMemo(() => {
    return tableRows.filter((lead) => {
      if (filters.leadOwner !== "All" && lead.crm_data.lead_owner !== filters.leadOwner) {
        return false
      }
      if (filters.leadStatus !== "All" && lead.crm_data.lead_status !== filters.leadStatus) {
        return false
      }
      if (filters.fitScore !== "All" && lead.qualification.label !== filters.fitScore) {
        return false
      }
      return true
    })
  }, [tableRows, filters])

  // Calculate metrics
  const metrics = useMemo(() => {
    const totalLeads = tableRows.length
    const highFitLeads = tableRows.filter((l) => l.qualification?.label === "High").length
    const openLeads = tableRows.filter((l) => l.crm_data?.lead_status === "Open").length
    const inProgressLeads = tableRows.filter((l) => l.crm_data?.lead_status === "In Progress").length

    return {
      totalLeads,
      highFitLeads,
      openLeads,
      inProgressLeads,
    }
  }, [tableRows])

  // Get unique lead owners for filter
  const leadOwners = useMemo(() => {
    const owners = new Set(tableRows.map((l) => l.crm_data.lead_owner).filter(Boolean))
    return ["All", ...Array.from(owners).sort()]
  }, [tableRows])

  // Handle lead update
  const handleUpdateLead = async (id: string, updates: Partial<LeadTableRow["crm_data"]>) => {
    try {
      // Optimistic update - update local state immediately (but NOT selectedLead to avoid re-render)
      if (leadsData) {
        const updatedLeads = leadsData.leads.map(lead => {
          // Use the UUID from Supabase, not a generated compound ID
          if (lead.id === id) {
            return {
              ...lead,
              crm_data: {
                ...lead.crm_data,
                ...updates,
              }
            }
          }
          return lead
        })

        setLeadsData({
          ...leadsData,
          leads: updatedLeads
        })

        // Do NOT update selectedLead here - let the panel manage its own state
        // This prevents the panel from re-rendering and losing scroll position
      }

      const response = await fetch("/api/leads", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, updates }),
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.message || "Failed to update lead")
      }

      // Silently refresh data in background without updating selectedLead
      const fileContents = await (await fetch("/api/leads")).json()
      if (fileContents.success) {
        setLeadsData(fileContents.data)
      }
    } catch (err) {
      console.error("Error updating lead:", err)
      alert(err instanceof Error ? err.message : "Failed to update lead")
      // Revert optimistic update on error by refetching
      await fetchLeads()
    }
  }

  const handleLeadClick = (lead: LeadTableRow) => {
    setSelectedLead(lead)
    setIsPanelOpen(true)
  }

  const handleClosePanel = () => {
    setIsPanelOpen(false)
    setTimeout(() => setSelectedLead(null), 300)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600">Loading leads...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <Button onClick={fetchLeads}>Retry</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-12">
      {/* Header */}
      <header className="bg-white border-b sticky top-0 z-30">
        <div className="max-w-[1600px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Instalily Lead Dashboard
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                DuPont Tedlar • AI-Powered Lead Intelligence
              </p>
            </div>
            <Button onClick={fetchLeads} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-[1600px] mx-auto px-6 py-6">
        {/* Last Data Pull Timestamp */}
        <div className="mb-4 text-sm text-gray-600">
          Last data pull: {formatDate(leadsData?.generated_at ?? null)} •{" "}
          Pipeline version {leadsData?.pipeline_version}
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Leads</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">
                    {metrics.totalLeads}
                  </p>
                </div>
                <Users className="w-10 h-10 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">High Fit Leads</p>
                  <p className="text-3xl font-bold text-green-600 mt-1">
                    {metrics.highFitLeads}
                  </p>
                </div>
                <Target className="w-10 h-10 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Open Leads</p>
                  <p className="text-3xl font-bold text-blue-600 mt-1">
                    {metrics.openLeads}
                  </p>
                </div>
                <Clock className="w-10 h-10 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">In Progress</p>
                  <p className="text-3xl font-bold text-purple-600 mt-1">
                    {metrics.inProgressLeads}
                  </p>
                </div>
                <TrendingUp className="w-10 h-10 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  Lead Owner
                </label>
                <Select
                  value={filters.leadOwner}
                  onChange={(e) =>
                    setFilters({ ...filters, leadOwner: e.target.value })
                  }
                >
                  {leadOwners.map((owner) => (
                    <option key={owner} value={owner}>
                      {owner}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  Lead Status
                </label>
                <Select
                  value={filters.leadStatus}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      leadStatus: e.target.value as LeadStatus | "All",
                    })
                  }
                >
                  <option value="All">All</option>
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Unqualified">Unqualified</option>
                  <option value="Closed">Closed</option>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 block mb-2">
                  Fit Score
                </label>
                <Select
                  value={filters.fitScore}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      fitScore: e.target.value as FitScoreLabel | "All",
                    })
                  }
                >
                  <option value="All">All</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </Select>
              </div>

              <div className="flex items-end">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowScoreInfo(!showScoreInfo)}
                >
                  <Info className="w-4 h-4 mr-2" />
                  Score Info
                </Button>
              </div>
            </div>

            {/* Score Breakdown Info */}
            {showScoreInfo && (
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <h4 className="text-sm font-semibold text-gray-900 mb-2">
                  Fit Score Calculation
                </h4>
                <div className="space-y-1 text-sm text-gray-700">
                  <p>
                    <strong>Industry Fit (30%):</strong> Core business alignment with
                    large-format signage, vehicle wraps, fleet graphics, or architectural
                    graphics
                  </p>
                  <p>
                    <strong>Size & Revenue (20%):</strong> Company scale (Revenue &gt;$50M or
                    200+ employees preferred)
                  </p>
                  <p>
                    <strong>Strategic Relevance (30%):</strong> Use, specify, or produce
                    protective overlaminates / durable graphic films
                  </p>
                  <p>
                    <strong>Event Engagement (20%):</strong> Active participation in ISA,
                    PRINTING United, FESPA, SEGD events
                  </p>
                  <p className="mt-2 text-xs text-gray-600">
                    Score: High (≥70), Medium (40-69), Low (&lt;40)
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Lead Table */}
        <LeadTable
          leads={filteredLeads}
          onLeadClick={handleLeadClick}
          onUpdateLead={handleUpdateLead}
        />
      </div>

      {/* Lead Detail Panel */}
      <LeadDetailPanel
        lead={selectedLead}
        isOpen={isPanelOpen}
        onClose={handleClosePanel}
        onUpdate={handleUpdateLead}
      />
    </div>
  )
}
