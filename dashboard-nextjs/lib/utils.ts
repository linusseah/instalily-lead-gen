import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, formatDistanceToNow, parseISO } from "date-fns"

/**
 * Utility function to merge Tailwind CSS classes
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Classify industry based on company description keywords
 */
export function classifyIndustry(description: string): string {
  const desc = description.toLowerCase()

  const industryPatterns = [
    { keywords: ["large-format", "large format", "wide-format", "wide format", "grand format"], industry: "Large-Format Printing" },
    { keywords: ["vehicle wrap", "fleet graphics", "vehicle graphic"], industry: "Vehicle Wraps & Fleet Graphics" },
    { keywords: ["architectural graphics", "architectural signage"], industry: "Architectural Graphics" },
    { keywords: ["sign", "signage"], industry: "Signage & Graphics" },
    { keywords: ["digital printing", "inkjet print"], industry: "Digital Printing" },
    { keywords: ["graphic solutions", "graphics solutions"], industry: "Graphics Solutions" },
    { keywords: ["distributor", "distribution"], industry: "Distribution & Supply" },
    { keywords: ["manufacturer", "manufacturing"], industry: "Manufacturing" },
    { keywords: ["print service", "printing service", "print provider"], industry: "Print Services" },
  ]

  for (const pattern of industryPatterns) {
    for (const keyword of pattern.keywords) {
      if (desc.includes(keyword)) {
        return pattern.industry
      }
    }
  }

  return "General Graphics & Printing"
}

/**
 * Generate a unique ID for a lead based on company name and decision maker
 */
export function generateLeadId(companyName: string, decisionMakerName: string | null): string {
  const baseName = decisionMakerName ? `${companyName}-${decisionMakerName}` : companyName
  return baseName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

/**
 * Format date for display
 */
export function formatDate(dateString: string | null): string {
  if (!dateString) return "—"

  try {
    const date = parseISO(dateString)
    return format(date, "MMM d, yyyy")
  } catch (e) {
    return dateString
  }
}

/**
 * Format date as relative time (e.g., "2 days ago")
 */
export function formatRelativeDate(dateString: string | null): string {
  if (!dateString) return "—"

  try {
    const date = parseISO(dateString)
    return formatDistanceToNow(date, { addSuffix: true })
  } catch (e) {
    return dateString
  }
}

/**
 * Get color class for fit score badge
 */
export function getFitScoreColor(label: "High" | "Medium" | "Low"): string {
  switch (label) {
    case "High":
      return "bg-green-100 text-green-800 border-green-200"
    case "Medium":
      return "bg-yellow-100 text-yellow-800 border-yellow-200"
    case "Low":
      return "bg-red-100 text-red-800 border-red-200"
  }
}

/**
 * Get color class for lead status badge
 */
export function getLeadStatusColor(status: string): string {
  switch (status) {
    case "Open":
      return "bg-blue-100 text-blue-800 border-blue-200"
    case "In Progress":
      return "bg-purple-100 text-purple-800 border-purple-200"
    case "Unqualified":
      return "bg-gray-100 text-gray-800 border-gray-200"
    case "Closed":
      return "bg-green-100 text-green-800 border-green-200"
    default:
      return "bg-gray-100 text-gray-800 border-gray-200"
  }
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    console.error("Failed to copy to clipboard:", err)
    return false
  }
}

/**
 * Truncate text to a specified length
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + "..."
}

/**
 * Calculate score breakdown percentages
 */
export function calculateScoreBreakdown(scores: {
  industry_fit: number
  size_and_revenue: number
  strategic_relevance: number
  event_engagement: number
}) {
  return {
    industry_fit: {
      score: scores.industry_fit,
      percentage: (scores.industry_fit / 10) * 100,
      weight: 30,
    },
    size_and_revenue: {
      score: scores.size_and_revenue,
      percentage: (scores.size_and_revenue / 10) * 100,
      weight: 20,
    },
    strategic_relevance: {
      score: scores.strategic_relevance,
      percentage: (scores.strategic_relevance / 10) * 100,
      weight: 30,
    },
    event_engagement: {
      score: scores.event_engagement,
      percentage: (scores.event_engagement / 10) * 100,
      weight: 20,
    },
  }
}
