"""
Supabase Client - Handles database operations for lead storage.

This client replaces flat JSON file storage with Supabase PostgreSQL.
Provides methods for:
- Creating pipeline runs
- Inserting leads
- Querying leads
- Updating CRM fields
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
from supabase import create_client, Client


class SupabaseClient:
    """Client for interacting with Supabase database."""

    def __init__(self):
        """Initialize Supabase client with credentials from environment."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env"
            )

        self.client: Client = create_client(supabase_url, supabase_key)

    def create_pipeline_run(self, pipeline_version: str, total_leads: int = 0) -> str:
        """
        Create a new pipeline run record.

        Args:
            pipeline_version: Version string (e.g. "1.0.0")
            total_leads: Number of leads generated (updated later)

        Returns:
            Pipeline run UUID
        """
        result = self.client.table("pipeline_runs").insert({
            "pipeline_version": pipeline_version,
            "total_leads": total_leads,
            "generated_at": datetime.now().isoformat()
        }).execute()

        return result.data[0]["id"]

    def update_pipeline_run_stats(
        self,
        pipeline_run_id: str,
        total_leads: int,
        high_fit: int,
        medium_fit: int,
        low_fit: int
    ):
        """Update pipeline run with final statistics."""
        self.client.table("pipeline_runs").update({
            "total_leads": total_leads,
            "high_fit_count": high_fit,
            "medium_fit_count": medium_fit,
            "low_fit_count": low_fit
        }).eq("id", pipeline_run_id).execute()

    def insert_lead(self, pipeline_run_id: str, lead_data: Dict) -> str:
        """
        Insert a single lead into the database.

        Args:
            pipeline_run_id: UUID of the pipeline run
            lead_data: Lead dict from agent pipeline (JSON structure)

        Returns:
            Lead UUID
        """
        # Extract searchable fields for denormalization
        company = lead_data.get("company", {})
        decision_maker = lead_data.get("decision_maker") or {}
        industry_engagement = lead_data.get("industry_engagement") or {}
        qualification = lead_data.get("qualification", {})
        crm_data = lead_data.get("crm_data", {})

        lead_row = {
            "pipeline_run_id": pipeline_run_id,

            # Denormalized searchable fields
            "company_name": company.get("name"),
            "decision_maker_name": decision_maker.get("name"),
            "decision_maker_title": decision_maker.get("title"),
            "decision_maker_linkedin": decision_maker.get("linkedin"),
            "decision_maker_email": decision_maker.get("email"),
            "decision_maker_phone": decision_maker.get("phone"),

            # Industry engagement (new schema)
            "industry_engagement": industry_engagement.get("summary"),
            "engagement_confidence": industry_engagement.get("confidence"),

            "qualification_score": int(qualification.get("weighted_total")) if qualification.get("weighted_total") else None,
            "qualification_label": qualification.get("label"),

            # CRM fields
            "lead_status": crm_data.get("lead_status", "Open"),
            "lead_owner": crm_data.get("lead_owner", ""),
            "last_interaction_date": crm_data.get("last_interaction_date"),
            "notes": crm_data.get("notes", ""),

            # Full nested data as JSONB
            "company_data": company,
            "qualification_data": qualification,
            "outreach_data": lead_data.get("outreach"),
            "decision_maker_data": decision_maker,
        }

        result = self.client.table("leads").insert(lead_row).execute()
        return result.data[0]["id"]

    def insert_leads_batch(self, pipeline_run_id: str, leads: List[Dict]) -> List[str]:
        """
        Insert multiple leads in a single batch operation.

        Args:
            pipeline_run_id: UUID of the pipeline run
            leads: List of lead dicts

        Returns:
            List of lead UUIDs
        """
        lead_rows = []
        for lead_data in leads:
            company = lead_data.get("company", {})
            decision_maker = lead_data.get("decision_maker") or {}
            industry_engagement = lead_data.get("industry_engagement") or {}
            qualification = lead_data.get("qualification", {})
            crm_data = lead_data.get("crm_data", {})

            lead_rows.append({
                "pipeline_run_id": pipeline_run_id,
                "company_name": company.get("name"),
                "decision_maker_name": decision_maker.get("name"),
                "decision_maker_title": decision_maker.get("title"),
                "decision_maker_linkedin": decision_maker.get("linkedin"),
                "decision_maker_email": decision_maker.get("email"),
                "decision_maker_phone": decision_maker.get("phone"),
                # Industry engagement (new schema)
                "industry_engagement": industry_engagement.get("summary"),
                "engagement_confidence": industry_engagement.get("confidence"),
                "qualification_score": int(qualification.get("weighted_total")) if qualification.get("weighted_total") else None,
                "qualification_label": qualification.get("label"),
                "lead_status": crm_data.get("lead_status", "Open"),
                "lead_owner": crm_data.get("lead_owner", ""),
                "last_interaction_date": crm_data.get("last_interaction_date"),
                "notes": crm_data.get("notes", ""),
                "company_data": company,
                "qualification_data": qualification,
                "outreach_data": lead_data.get("outreach"),
                "decision_maker_data": decision_maker,
            })

        result = self.client.table("leads").insert(lead_rows).execute()
        return [row["id"] for row in result.data]

    def get_all_leads(self) -> List[Dict]:
        """
        Fetch all leads from database.

        Returns:
            List of lead dicts in dashboard format
        """
        result = self.client.table("leads").select("*").order("created_at", desc=True).execute()

        # Transform database rows back to dashboard format
        leads = []
        for row in result.data:
            lead = {
                "id": row["id"],
                "company": row["company_data"],
                "decision_maker": row["decision_maker_data"],
                "industry_engagement": {
                    "summary": row.get("industry_engagement", ""),
                    "confidence": row.get("engagement_confidence", "inferred")
                } if row.get("industry_engagement") else None,
                "qualification": row["qualification_data"],
                "outreach": row["outreach_data"],
                "crm_data": {
                    "lead_status": row["lead_status"],
                    "lead_owner": row["lead_owner"],
                    "last_interaction_date": row["last_interaction_date"],
                    "created_date": row["created_at"],
                    "notes": row["notes"]
                }
            }
            leads.append(lead)

        return leads

    def get_latest_pipeline_run(self) -> Optional[Dict]:
        """Get the most recent pipeline run metadata."""
        result = self.client.table("pipeline_runs").select("*").order("created_at", desc=True).limit(1).execute()

        if result.data:
            return result.data[0]
        return None

    def check_duplicate_lead(self, company_name: str, decision_maker_name: str) -> bool:
        """
        Check if a lead already exists in the database.

        Args:
            company_name: Company name
            decision_maker_name: Decision maker's name

        Returns:
            True if duplicate exists, False otherwise
        """
        result = self.client.table("leads").select("id").eq("company_name", company_name).eq("decision_maker_name", decision_maker_name).execute()

        return len(result.data) > 0

    def update_lead_crm_data(self, lead_id: str, updates: Dict) -> bool:
        """
        Update CRM fields for a lead.

        Args:
            lead_id: Lead UUID
            updates: Dict with CRM field updates (lead_status, lead_owner, etc.)

        Returns:
            True if successful
        """
        # Update the lead row
        self.client.table("leads").update(updates).eq("id", lead_id).execute()

        # Log the update in audit table
        for field_name, new_value in updates.items():
            self.client.table("lead_updates").insert({
                "lead_id": lead_id,
                "field_name": field_name,
                "new_value": str(new_value) if new_value is not None else None
            }).execute()

        return True


if __name__ == "__main__":
    # Test connection
    from dotenv import load_dotenv
    load_dotenv()

    client = SupabaseClient()
    print("✓ Supabase client initialized successfully")

    # Test creating a pipeline run
    run_id = client.create_pipeline_run("1.0.0-test")
    print(f"✓ Created test pipeline run: {run_id}")
