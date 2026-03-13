"use client"

import { useState } from "react"
import { ExternalLink, ChevronDown, ChevronUp } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Select } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import type { LeadTableRow, LeadStatus } from "@/lib/types"
import {
  formatDate,
  getFitScoreColor,
  getLeadStatusColor,
  classifyIndustry,
} from "@/lib/utils"

interface LeadTableProps {
  leads: LeadTableRow[]
  onLeadClick: (lead: LeadTableRow) => void
  onUpdateLead: (id: string, updates: Partial<LeadTableRow["crm_data"]>) => Promise<void>
}

type SortField = "name" | "company" | "fit_score" | "created_date" | "last_interaction_date"
type SortDirection = "asc" | "desc"

export function LeadTable({ leads, onLeadClick, onUpdateLead }: LeadTableProps) {
  const [sortField, setSortField] = useState<SortField>("fit_score")
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc")
  const [editingCell, setEditingCell] = useState<{ leadId: string; field: string } | null>(null)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("desc")
    }
  }

  const sortedLeads = [...leads].sort((a, b) => {
    let aValue: any
    let bValue: any

    switch (sortField) {
      case "name":
        aValue = a.decision_maker?.name ?? ""
        bValue = b.decision_maker?.name ?? ""
        break
      case "company":
        aValue = a.company.name
        bValue = b.company.name
        break
      case "fit_score":
        aValue = a.qualification.weighted_total
        bValue = b.qualification.weighted_total
        break
      case "created_date":
        aValue = a.crm_data?.created_date ? new Date(a.crm_data.created_date).getTime() : 0
        bValue = b.crm_data?.created_date ? new Date(b.crm_data.created_date).getTime() : 0
        break
      case "last_interaction_date":
        aValue = a.crm_data.last_interaction_date
          ? new Date(a.crm_data.last_interaction_date).getTime()
          : 0
        bValue = b.crm_data.last_interaction_date
          ? new Date(b.crm_data.last_interaction_date).getTime()
          : 0
        break
      default:
        return 0
    }

    if (aValue < bValue) return sortDirection === "asc" ? -1 : 1
    if (aValue > bValue) return sortDirection === "asc" ? 1 : -1
    return 0
  })

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === "asc" ? (
      <ChevronUp className="inline w-4 h-4 ml-1" />
    ) : (
      <ChevronDown className="inline w-4 h-4 ml-1" />
    )
  }

  const handleInlineEdit = async (
    leadId: string,
    field: "lead_status" | "lead_owner",
    value: string
  ) => {
    await onUpdateLead(leadId, { [field]: value })
    setEditingCell(null)
  }

  return (
    <div className="overflow-x-auto border rounded-lg">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th
              className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort("name")}
            >
              Name <SortIcon field="name" />
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">Title</th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">Lead Status</th>
            <th
              className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort("company")}
            >
              Company <SortIcon field="company" />
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">Website</th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">Industry</th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">Lead Owner</th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">Email</th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">Phone</th>
            <th className="px-4 py-3 text-left font-medium text-gray-700">LinkedIn</th>
            <th
              className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort("last_interaction_date")}
            >
              Last Interaction <SortIcon field="last_interaction_date" />
            </th>
            <th
              className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort("created_date")}
            >
              Created <SortIcon field="created_date" />
            </th>
            <th
              className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort("fit_score")}
            >
              Fit Score <SortIcon field="fit_score" />
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {sortedLeads.map((lead) => (
            <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3">
                <button
                  onClick={() => onLeadClick(lead)}
                  className="text-blue-600 hover:text-blue-800 hover:underline font-medium text-left"
                >
                  {lead.decision_maker?.name ?? "—"}
                </button>
              </td>
              <td className="px-4 py-3 text-gray-700">
                {lead.decision_maker?.title ?? "—"}
              </td>
              <td className="px-4 py-3">
                {editingCell?.leadId === lead.id && editingCell?.field === "lead_status" ? (
                  <Select
                    value={lead.crm_data.lead_status}
                    onChange={(e) =>
                      handleInlineEdit(lead.id, "lead_status", e.target.value as LeadStatus)
                    }
                    onBlur={() => setEditingCell(null)}
                    autoFocus
                    className="w-full min-w-[140px]"
                  >
                    <option value="Open">Open</option>
                    <option value="In Progress">In Progress</option>
                    <option value="Unqualified">Unqualified</option>
                    <option value="Closed">Closed</option>
                  </Select>
                ) : (
                  <Badge
                    className={getLeadStatusColor(lead.crm_data.lead_status)}
                    onClick={() =>
                      setEditingCell({ leadId: lead.id, field: "lead_status" })
                    }
                  >
                    {lead.crm_data.lead_status}
                  </Badge>
                )}
              </td>
              <td className="px-4 py-3 font-medium text-gray-900">
                {lead.company.name}
                {lead.company.competitor_flag && (
                  <span className="ml-2 text-xs text-orange-600 font-semibold">
                    COMPETITOR
                  </span>
                )}
              </td>
              <td className="px-4 py-3">
                {lead.company.website ? (
                  <a
                    href={lead.company.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
                  >
                    Link <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  "—"
                )}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {classifyIndustry(lead.company.description)}
              </td>
              <td className="px-4 py-3">
                {editingCell?.leadId === lead.id && editingCell?.field === "lead_owner" ? (
                  <Input
                    type="text"
                    defaultValue={lead.crm_data.lead_owner}
                    onBlur={(e) =>
                      handleInlineEdit(lead.id, "lead_owner", e.target.value)
                    }
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleInlineEdit(
                          lead.id,
                          "lead_owner",
                          e.currentTarget.value
                        )
                      }
                    }}
                    autoFocus
                    className="w-full min-w-[140px]"
                  />
                ) : (
                  <div
                    onClick={() =>
                      setEditingCell({ leadId: lead.id, field: "lead_owner" })
                    }
                    className="cursor-text hover:bg-gray-100 px-2 py-1 rounded min-h-[32px] flex items-center"
                  >
                    {lead.crm_data.lead_owner || "—"}
                  </div>
                )}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {lead.decision_maker?.email ?? "—"}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {lead.decision_maker?.phone ?? "—"}
              </td>
              <td className="px-4 py-3">
                {lead.decision_maker?.linkedin ? (
                  <a
                    href={lead.decision_maker.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
                  >
                    Link <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  "—"
                )}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {formatDate(lead.crm_data?.last_interaction_date || null)}
              </td>
              <td className="px-4 py-3 text-gray-700">
                {formatDate(lead.crm_data?.created_date || null)}
              </td>
              <td className="px-4 py-3">
                <Badge className={getFitScoreColor(lead.qualification.label)}>
                  {lead.qualification.label} ({lead.qualification.weighted_total})
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {sortedLeads.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No leads match your filters
        </div>
      )}
    </div>
  )
}
