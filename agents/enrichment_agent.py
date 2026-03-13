"""
Enrichment Agent - Uses Claude API with web search to enrich and qualify companies.

This agent has two phases:
Phase A: Company Enrichment (revenue, size, strategic fit, decision-makers)
Phase B: Qualification Scoring (4-criterion rubric → score → label)
"""

import os
import sys
from typing import List, Dict
from anthropic import Anthropic

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Exa client
from integrations.exa_client import ExaClient

DEFAULT_MODEL_FALLBACKS = [
    # Keep this list conservative; prefer env var overrides when possible.
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]


def resolve_anthropic_model(client: Anthropic) -> str:
    """
    Pick an Anthropic model id.

    Priority:
      1) ANTHROPIC_MODEL env var
      2) Best match from `client.models.list()` (if available)
      3) Static fallbacks
    """
    override = (os.getenv("ANTHROPIC_MODEL") or "").strip()
    if override:
        return override

    # Try to discover available models for this API key at runtime.
    try:
        page = client.models.list(limit=100)

        # anthropic pagination objects typically expose `.data`, but be defensive.
        models = []
        if hasattr(page, "data") and page.data:
            models = list(page.data)
        else:
            try:
                models = list(page)
            except TypeError:
                models = []

        model_ids = [m.id for m in models if getattr(m, "id", None)]

        def rank(model_id: str) -> tuple:
            mid = model_id.lower()
            return (
                "claude" in mid,
                "sonnet" in mid,
                "latest" in mid,
                # Prefer newer families if present (best-effort).
                "claude-4" in mid,
                "claude-3-7" in mid,
                "claude-3-5" in mid,
                "claude-3" in mid,
            )

        if model_ids:
            return sorted(model_ids, key=rank, reverse=True)[0]
    except Exception:
        # No network, invalid key, or models.list not allowed for this key.
        pass

    return DEFAULT_MODEL_FALLBACKS[0]


# ICP Rubric Weights
RUBRIC_WEIGHTS = {
    "industry_fit": 0.30,
    "size_and_revenue": 0.20,
    "strategic_relevance": 0.30,
    "event_engagement": 0.20
}

# Competitor list
COMPETITORS = ["Avery Dennison", "3M"]


def run_enrichment(research_results: Dict) -> List[Dict]:
    """
    Main entry point for enrichment agent.

    Args:
        research_results: Output from research agent with events and companies

    Returns:
        List of enriched and qualified lead dicts
    """
    print("Initializing Claude client...")
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = resolve_anthropic_model(client)
    print(f"Using Anthropic model: {model}")

    print("Initializing Exa client for web search...")
    exa_client = ExaClient()

    companies = research_results.get('companies', [])
    enriched_leads = []

    for i, company_data in enumerate(companies, 1):
        # Normalize company data structure from new Research Agent
        # New format: {company_name, website}
        # Enrichment Agent expects: {name, website}
        normalized_company = {
            "name": company_data.get('company_name', company_data.get('name', 'Unknown')),
            "website": company_data.get('website', ''),
            # No event data from Research Agent anymore - will be enriched later
            "event": {
                "name": "N/A",
                "date": "N/A",
                "location": "N/A",
                "relevance": "Event context to be determined during enrichment"
            }
        }

        print(f"\n[{i}/{len(companies)}] Processing: {normalized_company['name']}")

        try:
            # Phase A: Enrich
            print("  Phase A: Enriching company data...")
            enriched_company = enrich_company(client, exa_client, normalized_company, model=model)

            if enriched_company['enrichment_status'] != 'success':
                print(f"  ✗ Enrichment failed, skipping qualification")
                lead = build_lead_object(normalized_company, enriched_company, None, None)
                enriched_leads.append(lead)
                continue

            # Phase B: Qualify
            print("  Phase B: Scoring against ICP rubric...")
            qualification = qualify_company(client, enriched_company, model=model)

            # Check for competitor flag
            competitor_flag = is_competitor(enriched_company['name'])
            enriched_company['competitor_flag'] = competitor_flag

            if competitor_flag:
                print(f"  ⚠ Competitor detected: {enriched_company['name']}")

            # Build complete lead object
            lead = build_lead_object(
                normalized_company,
                enriched_company,
                qualification,
                enriched_company.get('decision_maker')
            )

            enriched_leads.append(lead)

            # Log result
            score = qualification.get('weighted_total', 0)
            label = qualification.get('label', 'Unknown')
            print(f"  ✓ Score: {score}/100 ({label})")

        except Exception as e:
            print(f"  ✗ Error processing {normalized_company['name']}: {e}")
            # Add failed lead with minimal data
            lead = {
                "event": normalized_company.get('event', {}),
                "company": {
                    "name": normalized_company['name'],
                    "website": normalized_company.get('website', ''),
                    "enrichment_status": "failed",
                    "error": str(e)
                },
                "qualification": {"label": "Unknown", "rationale": "Enrichment failed"},
                "decision_maker": None,
                "outreach": None
            }
            enriched_leads.append(lead)
            continue

    return enriched_leads


def enrich_company(client: Anthropic, exa_client: ExaClient, company_data: Dict, *, model: str) -> Dict:
    """
    Phase A: Enrich company data using Exa web search + Claude analysis.

    Args:
        client: Anthropic client
        exa_client: Exa API client
        company_data: Basic company info from research agent
        model: Anthropic model ID to use

    Returns:
        Enriched company dict
    """
    company_name = company_data['name']
    website = company_data.get('website', '')

    # PRIORITY 1: Find decision-maker contact info
    # PRIORITY 2: Verify company details
    # PRIORITY 3: Verify event attendance if applicable

    event_name = company_data.get('event', {}).get('name', 'N/A')

    # Build targeted search queries with CONTACT FOCUS
    search_queries = [
        f"{company_name} CEO President VP Director leadership team",
        f"{company_name} VP Product Development Director Operations executives",
        f"{company_name} VP Procurement Director R&D contact information",
        f"{company_name} company revenue size employees headquarters",
        f"{company_name} graphics signage protective films overlaminates products",
    ]

    # Add event-specific search if event is known
    if event_name != "N/A" and event_name != "Industry Research":
        search_queries.insert(0, f"{company_name} {event_name} exhibitor sponsor attendee")
        search_queries.insert(1, f"{company_name} {event_name} booth representative speaker")

    web_context = []
    for query in search_queries:
        results = exa_client.search(query, num_results=3, type="neural")
        for result in results:
            web_context.append(f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['text']}\n")

    web_context_str = "\n---\n".join(web_context[:15])  # More results to find contacts

    prompt = f"""You are enriching company data for a lead generation pipeline for DuPont Tedlar, which makes protective PVF films for graphics and signage applications.

**CRITICAL REQUIREMENT: This lead is ONLY valid if you can find a real decision-maker (name + title minimum).**

Company to research: {company_name}
Website: {website}
Associated Event: {event_name}

**Web search results:**
{web_context_str}

Based on the web search results above, provide:

1. **Revenue estimate** - Annual revenue or size estimate (e.g. "$50M-100M" or "500-1000 employees")
2. **Company size** - Employee count estimate
3. **Core business description** - What do they do? (2-3 sentences, focus on graphics/signage products)
4. **Strategic fit** - How does their business relate to protective films, overlaminates, or durable graphic materials for large-format signage, vehicle wraps, or architectural graphics?

5. **Event attendance verification** (ONLY if Associated Event is NOT "N/A" or "Industry Research"):
   - Did you find evidence in the search results that {company_name} is attending, exhibiting, sponsoring, or speaking at {event_name}?
   - Set event_verified to true ONLY if you found direct evidence (exhibitor list, sponsor announcement, speaker lineup, booth number, etc.)
   - Set event_verified to false if no evidence found
   - If false, set event_likelihood: "high", "medium", or "low" based on company profile fit with event

6. **Key decision-maker** (REQUIRED - THIS IS MANDATORY):
   - Find ONE relevant decision-maker (C-level, VP, or Director in Product, Procurement, R&D, Operations, or Sales)
   - Name: MUST be a real person's name found in search results
   - Title: MUST be their actual title
   - LinkedIn URL: ONLY if you find a real, complete LinkedIn profile URL in format https://www.linkedin.com/in/[username]
   - **If you cannot find a real person with name + title, return null for decision_maker and set enrichment_status to "no_contact_found"**

Format your response as JSON:
{{
  "revenue_estimate": "...",
  "size": "...",
  "description": "...",
  "strategic_fit_rationale": "...",
  "event_verified": true or false or null,
  "event_likelihood": "high" or "medium" or "low" or null,
  "decision_maker": {{
    "name": "Full Name",
    "title": "Exact Title",
    "linkedin": "https://www.linkedin.com/in/username" or null
  }} OR null,
  "enrichment_status": "success" or "no_contact_found"
}}

**STRICT RULES:**
1. decision_maker MUST have a real name and title from search results - NO GUESSING
2. If you cannot find contact info, set decision_maker to null and enrichment_status to "no_contact_found"
3. LinkedIn URL must be exact format - do NOT construct or guess
4. event_verified is true ONLY if you found direct evidence of attendance
5. If Associated Event is "N/A" or "Industry Research", set event_verified and event_likelihood to null

The lead is worthless without a real contact. Be strict."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        result_text = ""
        for block in response.content:
            if block.type == "text":
                result_text += block.text

        # Parse JSON (simple extraction)
        import json
        # Try to find JSON in the response
        start_idx = result_text.find('{')
        end_idx = result_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = result_text[start_idx:end_idx]
            data = json.loads(json_str)

            return {
                "name": company_name,
                "website": website,
                "revenue_estimate": data.get("revenue_estimate", "Unknown"),
                "size": data.get("size", "Unknown"),
                "description": data.get("description", "No description available"),
                "strategic_fit_rationale": data.get("strategic_fit_rationale", ""),
                "decision_maker": data.get("decision_maker"),
                "enrichment_status": "success"
            }
        else:
            raise ValueError("No JSON found in response")

    except Exception as e:
        print(f"    Enrichment error: {e}")
        return {
            "name": company_name,
            "website": website,
            "enrichment_status": "failed",
            "error": str(e)
        }


def qualify_company(client: Anthropic, enriched_company: Dict, *, model: str) -> Dict:
    """
    Phase B: Score company against ICP rubric.

    Rubric (0-10 each):
    - Industry Fit (30%): Large-format signage, vehicle wraps, fleet graphics, architectural graphics
    - Size & Revenue (20%): >$50M revenue or 200+ employees preferred
    - Strategic Relevance (30%): Use/produce protective overlaminates or durable graphic films
    - Event Engagement (20%): Active in ISA, PRINTING United, FESPA, SEGD

    Args:
        client: Anthropic client
        enriched_company: Enriched company data

    Returns:
        Qualification dict with scores, total, label, and rationale
    """

    prompt = f"""You are scoring a company against DuPont Tedlar's Ideal Customer Profile (ICP) for protective films in the graphics and signage industry.

**Company Data:**
- Name: {enriched_company['name']}
- Revenue: {enriched_company['revenue_estimate']}
- Size: {enriched_company['size']}
- Description: {enriched_company['description']}
- Strategic Fit: {enriched_company['strategic_fit_rationale']}

**Scoring Rubric (score each 0-10):**

1. **Industry Fit (30% weight)**: Is core business in large-format signage, vehicle wraps, fleet graphics, or architectural graphics?
   - 9-10: Core business is directly in these categories
   - 6-8: Significant product lines in these areas
   - 3-5: Adjacent or minor involvement
   - 0-2: Not in these industries

2. **Size & Revenue (20% weight)**: Revenue >$50M or 200+ employees preferred
   - 9-10: >$500M revenue or 1000+ employees
   - 6-8: $50M-500M revenue or 200-1000 employees
   - 3-5: $10M-50M revenue or 50-200 employees
   - 0-2: <$10M revenue or <50 employees

3. **Strategic Relevance (30% weight)**: Do they use, specify, or produce protective overlaminates/durable graphic films that Tedlar could supply?
   - 9-10: Direct use case for protective films in their products
   - 6-8: Strong potential application
   - 3-5: Possible application
   - 0-2: No clear fit

4. **Event & Association Engagement (20% weight)**: Active in ISA, PRINTING United, FESPA, SEGD?
   - 9-10: Exhibitor at multiple key events
   - 6-8: Active in 1-2 events/associations
   - 3-5: Some industry presence
   - 0-2: No visible event engagement

**Output Format (JSON):**
{{
  "scores": {{
    "industry_fit": X,
    "size_and_revenue": X,
    "strategic_relevance": X,
    "event_engagement": X
  }},
  "rationale": "1-2 sentence summary of why this score was given"
}}

Be objective and precise. Consider the data provided."""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON
        result_text = ""
        for block in response.content:
            if block.type == "text":
                result_text += block.text

        import json
        start_idx = result_text.find('{')
        end_idx = result_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = result_text[start_idx:end_idx]
            data = json.loads(json_str)

            scores = data.get('scores', {})

            # Calculate weighted total
            weighted_total = (
                scores.get('industry_fit', 0) * RUBRIC_WEIGHTS['industry_fit'] +
                scores.get('size_and_revenue', 0) * RUBRIC_WEIGHTS['size_and_revenue'] +
                scores.get('strategic_relevance', 0) * RUBRIC_WEIGHTS['strategic_relevance'] +
                scores.get('event_engagement', 0) * RUBRIC_WEIGHTS['event_engagement']
            ) * 10

            # Determine label
            if weighted_total >= 70:
                label = "High"
            elif weighted_total >= 40:
                label = "Medium"
            else:
                label = "Low"

            return {
                "scores": scores,
                "weighted_total": round(weighted_total, 1),
                "label": label,
                "rationale": data.get('rationale', '')
            }
        else:
            raise ValueError("No JSON found in qualification response")

    except Exception as e:
        print(f"    Qualification error: {e}")
        return {
            "scores": {},
            "weighted_total": 0,
            "label": "Unknown",
            "rationale": f"Qualification failed: {str(e)}"
        }


def is_competitor(company_name: str) -> bool:
    """Check if company is a known competitor."""
    return any(comp.lower() in company_name.lower() for comp in COMPETITORS)


def build_lead_object(
    company_data: Dict,
    enriched_company: Dict,
    qualification: Dict,
    decision_maker: Dict
) -> Dict:
    """
    Build the complete lead object matching the schema.

    Args:
        company_data: Original research data
        enriched_company: Enriched company info
        qualification: Qualification scores
        decision_maker: Decision maker info

    Returns:
        Complete lead dict
    """
    return {
        "event": company_data.get('event', {}),
        "company": {
            "name": enriched_company.get('name', company_data['name']),
            "website": enriched_company.get('website', ''),
            "revenue_estimate": enriched_company.get('revenue_estimate', 'Unknown'),
            "size": enriched_company.get('size', 'Unknown'),
            "description": enriched_company.get('description', ''),
            "competitor_flag": enriched_company.get('competitor_flag', False),
            "enrichment_status": enriched_company.get('enrichment_status', 'failed')
        },
        "qualification": qualification if qualification else {
            "label": "Unknown",
            "rationale": "Qualification not completed"
        },
        "decision_maker": {
            "name": decision_maker.get('name') if decision_maker else None,
            "title": decision_maker.get('title') if decision_maker else None,
            "linkedin": decision_maker.get('linkedin') if decision_maker else None,
            "source": "web_search",
            "email": None,
            "phone": None,
            "clay_stub": "STUB: Clay API would waterfall-enrich contact details across 50+ data sources here",
            "linkedin_stub": "STUB: LinkedIn Sales Navigator API would verify contact and pull email/phone here"
        } if decision_maker else None,
        "outreach": None  # Will be filled by outreach agent
    }


if __name__ == "__main__":
    # Test enrichment agent
    test_data = {
        "events": [{"name": "ISA Sign Expo 2026", "date": "April 2026", "location": "Orlando, FL"}],
        "companies": [
            {"name": "Avery Dennison Graphics Solutions", "website": "https://www.averydennison.com", "event": {}}
        ]
    }
    results = run_enrichment(test_data)
    print(f"\nEnriched {len(results)} companies")
