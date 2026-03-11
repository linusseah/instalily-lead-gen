"""
Instalily Lead Generation Pipeline
Main orchestrator that runs all three agents sequentially.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from agents.research_agent import run_research
from agents.enrichment_agent import run_enrichment
from agents.outreach_agent import run_outreach

# Load environment variables
load_dotenv()

# Configuration
OUTPUT_FILE = Path("data/leads.json")
PIPELINE_VERSION = "1.0.0"


def main():
    """
    Run the complete lead generation pipeline.

    Flow:
    1. Research Agent: Find events and companies via Exa API
    2. Enrichment Agent: Enrich + qualify companies via Claude API
    3. Outreach Agent: Draft personalized outreach via Claude API
    4. Save results to data/leads.json
    """

    print("=" * 80)
    print("INSTALILY LEAD GENERATION PIPELINE")
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
        print(f"✓ Found {len(research_results.get('events', []))} events")
        print(f"✓ Found {len(research_results.get('companies', []))} candidate companies")
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

    # Save results
    print("\n[FINAL] Saving results...")
    print("-" * 80)
    output = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_version": PIPELINE_VERSION,
        "leads": final_leads
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Saved {len(final_leads)} leads to {OUTPUT_FILE}")

    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)
    print(f"Total leads: {len(final_leads)}")
    print(f"High fit: {high_fit}")
    print(f"Medium fit: {medium_fit}")
    print(f"Low fit: {low_fit}")
    print(f"Outreach drafted: {drafted}")
    print(f"\nRun the dashboard with: streamlit run dashboard/app.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
