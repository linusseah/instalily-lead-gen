"""
Instalily Lead Generation Pipeline
Main orchestrator that runs all three agents sequentially.

Usage:
    python main.py              # Run full pipeline
    python main.py --test       # Quick test with 3 companies
    python main.py --limit 5    # Process only 5 companies
"""

import json
import os
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from agents.research_agent import run_research
from agents.enrichment_agent import run_enrichment
from agents.outreach_agent import run_outreach
from integrations.supabase_client import SupabaseClient

# Load environment variables
load_dotenv()

# Configuration
OUTPUT_FILE = Path("data/leads.json")
PIPELINE_VERSION = "1.0.0"
MIN_QUALIFICATION_SCORE = 50  # Only keep leads scoring 50+ (Medium or High)


def main():
    """
    Run the complete lead generation pipeline.

    Flow:
    1. Research Agent: Find events and companies via Exa API
    2. Enrichment Agent: Enrich + qualify companies via Claude API
    3. Outreach Agent: Draft personalized outreach via Claude API
    4. Save results to data/leads.json
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Instalily lead generation pipeline')
    parser.add_argument('--test', action='store_true', help='Quick test mode (3 companies)')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    args = parser.parse_args()

    # Determine limit
    if args.test:
        company_limit = 3
        mode = "TEST MODE"
    elif args.limit:
        company_limit = args.limit
        mode = f"LIMITED MODE ({company_limit} companies)"
    else:
        company_limit = None
        mode = "FULL PIPELINE"

    print("=" * 80)
    print(f"INSTALILY LEAD GENERATION PIPELINE — {mode}")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Validate API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY not found in environment")
    if not os.getenv("EXA_API_KEY"):
        raise ValueError("EXA_API_KEY not found in environment")

    # Step 1: Research Agent
    print("\n[1/3] Running Research Agent...")
    print("-" * 80)
    try:
        research_results = run_research()
        print(f"✓ Found {len(research_results.get('companies', []))} candidate companies")

        # Limit companies if in test/limited mode
        if company_limit:
            original_count = len(research_results.get('companies', []))
            research_results['companies'] = research_results['companies'][:company_limit]
            print(f"⚠ Limited to {company_limit} companies for testing (found {original_count} total)")
    except Exception as e:
        print(f"✗ Research Agent failed: {e}")
        raise

    # Step 2: Enrichment Agent
    print("\n[2/3] Running Enrichment Agent...")
    print("-" * 80)
    try:
        enriched_leads = run_enrichment(research_results)
        successful = sum(1 for lead in enriched_leads if lead.get('company', {}).get('enrichment_status') == 'success')
        print(f"✓ Enriched {successful}/{len(enriched_leads)} companies")

        high_fit = sum(1 for lead in enriched_leads if lead.get('qualification', {}).get('label') == 'High')
        medium_fit = sum(1 for lead in enriched_leads if lead.get('qualification', {}).get('label') == 'Medium')
        low_fit = sum(1 for lead in enriched_leads if lead.get('qualification', {}).get('label') == 'Low')
        print(f"✓ Qualification: {high_fit} High, {medium_fit} Medium, {low_fit} Low")

        # Filter out leads WITHOUT valid contacts (CRITICAL FILTER)
        before_contact_filter = len(enriched_leads)
        enriched_leads = [
            lead for lead in enriched_leads
            if lead.get('decision_maker') is not None
            and lead.get('decision_maker', {}).get('name') is not None
            and lead.get('decision_maker', {}).get('title') is not None
        ]
        no_contact_count = before_contact_filter - len(enriched_leads)
        if no_contact_count > 0:
            print(f"✓ Filtered out {no_contact_count} leads without valid contact info (REQUIRED: name + title minimum)")

        # Filter out low-scoring leads
        before_score_filter = len(enriched_leads)
        enriched_leads = [
            lead for lead in enriched_leads
            if lead.get('qualification', {}).get('weighted_total', 0) >= MIN_QUALIFICATION_SCORE
        ]
        low_score_count = before_score_filter - len(enriched_leads)
        if low_score_count > 0:
            print(f"✓ Filtered out {low_score_count} low-scoring leads (score < {MIN_QUALIFICATION_SCORE})")

    except Exception as e:
        print(f"✗ Enrichment Agent failed: {e}")
        raise

    # Step 3: Outreach Agent
    print("\n[3/3] Running Outreach Agent...")
    print("-" * 80)
    try:
        final_leads = run_outreach(enriched_leads)
        drafted = sum(1 for lead in final_leads if lead.get('outreach', {}).get('status') == 'draft')
        print(f"✓ Drafted {drafted} outreach messages")
    except Exception as e:
        print(f"✗ Outreach Agent failed: {e}")
        raise

    # Save results to Supabase AND JSON (dual-write for backup)
    print("\n[FINAL] Saving results...")
    print("-" * 80)

    # Calculate final stats
    high_fit_final = sum(1 for lead in final_leads if lead.get('qualification', {}).get('label') == 'High')
    medium_fit_final = sum(1 for lead in final_leads if lead.get('qualification', {}).get('label') == 'Medium')
    low_fit_final = sum(1 for lead in final_leads if lead.get('qualification', {}).get('label') == 'Low')

    # Write to Supabase
    try:
        print("  Writing to Supabase database...")
        supabase = SupabaseClient()

        # Filter out duplicates before inserting
        non_duplicate_leads = []
        duplicates_count = 0

        for lead in final_leads:
            company_name = lead.get("company", {}).get("name")
            dm_name = lead.get("decision_maker", {}).get("name")

            if company_name and dm_name:
                if supabase.check_duplicate_lead(company_name, dm_name):
                    duplicates_count += 1
                    continue

            non_duplicate_leads.append(lead)

        if duplicates_count > 0:
            print(f"  ⚠ Skipped {duplicates_count} duplicate leads")

        # Create pipeline run
        pipeline_run_id = supabase.create_pipeline_run(PIPELINE_VERSION, len(non_duplicate_leads))
        print(f"  ✓ Created pipeline run: {pipeline_run_id}")

        # Insert all non-duplicate leads in batch
        if non_duplicate_leads:
            lead_ids = supabase.insert_leads_batch(pipeline_run_id, non_duplicate_leads)
            print(f"  ✓ Inserted {len(lead_ids)} new leads to Supabase")

        # Update pipeline stats
        supabase.update_pipeline_run_stats(
            pipeline_run_id,
            len(final_leads),
            high_fit_final,
            medium_fit_final,
            low_fit_final
        )
        print(f"  ✓ Updated pipeline statistics")

    except Exception as e:
        print(f"  ⚠ Supabase write failed: {e}")
        print(f"  ⚠ Falling back to JSON-only storage")

    # Also save to JSON file as backup
    output = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_version": PIPELINE_VERSION,
        "leads": final_leads
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Saved {len(final_leads)} leads to {OUTPUT_FILE} (backup)")

    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"Total leads: {len(final_leads)}")
    print(f"High fit: {high_fit_final}")
    print(f"Medium fit: {medium_fit_final}")
    print(f"Low fit: {low_fit_final}")
    print(f"Outreach drafted: {drafted}")
    print(f"\nData stored in: Supabase + {OUTPUT_FILE} (backup)")
    print(f"Run the Next.js dashboard:")
    print(f"  cd dashboard-nextjs && npm run dev")
    print("=" * 80)


if __name__ == "__main__":
    main()
