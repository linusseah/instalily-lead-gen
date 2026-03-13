import { NextRequest, NextResponse } from "next/server"
import type { LeadsData, UpdateLeadRequest } from "@/lib/types"
import { supabase } from "@/lib/supabase"

/**
 * GET /api/leads
 * Returns all leads from Supabase database
 */
export async function GET() {
  try {
    // Fetch all leads from Supabase
    const { data: leads, error } = await supabase
      .from('leads')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) {
      console.error("Supabase error:", error)
      throw new Error(error.message)
    }

    // Fetch latest pipeline run metadata
    const { data: pipelineRun } = await supabase
      .from('pipeline_runs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(1)
      .single()

    // Transform Supabase rows to dashboard format
    const transformedLeads = leads.map((row: any) => ({
      id: row.id,
      company: row.company_data,
      decision_maker: row.decision_maker_data,
      event: row.event_data,
      qualification: row.qualification_data,
      outreach: row.outreach_data,
      crm_data: {
        lead_status: row.lead_status,
        lead_owner: row.lead_owner,
        last_interaction_date: row.last_interaction_date,
        created_date: row.created_at,
        notes: row.notes || ""
      }
    }))

    const data: LeadsData = {
      generated_at: pipelineRun?.generated_at || new Date().toISOString(),
      pipeline_version: pipelineRun?.pipeline_version || "1.0.0",
      leads: transformedLeads
    }

    return NextResponse.json({
      success: true,
      data,
    })
  } catch (error) {
    console.error("Error fetching leads from Supabase:", error)
    return NextResponse.json(
      {
        success: false,
        message: error instanceof Error ? error.message : "Failed to read leads data",
      },
      { status: 500 }
    )
  }
}

/**
 * PATCH /api/leads
 * Updates a specific lead's CRM data in Supabase
 */
export async function PATCH(request: NextRequest) {
  try {
    const body: UpdateLeadRequest = await request.json()
    const { id, updates } = body

    if (!id || !updates) {
      return NextResponse.json(
        {
          success: false,
          message: "Missing required fields: id and updates",
        },
        { status: 400 }
      )
    }

    // Update the lead in Supabase
    const { data: updatedLead, error } = await supabase
      .from('leads')
      .update(updates)
      .eq('id', id)
      .select()
      .single()

    if (error) {
      console.error("Supabase update error:", error)
      throw new Error(error.message)
    }

    if (!updatedLead) {
      return NextResponse.json(
        {
          success: false,
          message: `Lead with id "${id}" not found`,
        },
        { status: 404 }
      )
    }

    return NextResponse.json({
      success: true,
      message: "Lead updated successfully",
      lead: updatedLead,
    })
  } catch (error) {
    console.error("Error updating lead:", error)
    return NextResponse.json(
      {
        success: false,
        message: error instanceof Error ? error.message : "Failed to update lead",
      },
      { status: 500 }
    )
  }
}
