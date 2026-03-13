"""
Outreach Agent - Uses Claude API to draft personalized outreach messages.

This agent:
1. Takes enriched and qualified leads
2. For each lead with a decision-maker, drafts personalized outreach
3. Returns leads with outreach subject + message populated
"""

import os
import sys
from typing import List, Dict
from anthropic import Anthropic

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


def run_outreach(enriched_leads: List[Dict]) -> List[Dict]:
    """
    Main entry point for outreach agent.

    Args:
        enriched_leads: List of enriched and qualified leads

    Returns:
        List of leads with outreach messages drafted
    """
    print("Initializing Claude client...")
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = resolve_anthropic_model(client)
    print(f"Using Anthropic model: {model}")

    leads_with_outreach = []

    for i, lead in enumerate(enriched_leads, 1):
        company_name = lead['company']['name']
        print(f"\n[{i}/{len(enriched_leads)}] Drafting outreach for: {company_name}")

        # Skip if no decision maker or enrichment failed
        if not lead.get('decision_maker') or not lead['decision_maker'].get('name'):
            print(f"  ✗ No decision-maker found, skipping outreach")
            lead['outreach'] = {
                "subject": None,
                "message": None,
                "status": "no_decision_maker"
            }
            leads_with_outreach.append(lead)
            continue

        # Skip low-quality leads (optional - could still draft for Medium)
        qualification_label = lead.get('qualification', {}).get('label', 'Unknown')
        if qualification_label == 'Unknown':
            print(f"  ✗ Qualification failed, skipping outreach")
            lead['outreach'] = {
                "subject": None,
                "message": None,
                "status": "qualification_failed"
            }
            leads_with_outreach.append(lead)
            continue

        try:
            # Draft outreach
            outreach = draft_outreach_message(client, lead, model=model)
            lead['outreach'] = outreach
            print(f"  ✓ Outreach drafted")

        except Exception as e:
            print(f"  ✗ Error drafting outreach: {e}")
            lead['outreach'] = {
                "subject": None,
                "message": None,
                "status": "draft_failed",
                "error": str(e)
            }

        leads_with_outreach.append(lead)

    return leads_with_outreach


def draft_outreach_message(client: Anthropic, lead: Dict, *, model: str) -> Dict:
    """
    Draft personalized outreach message for a lead.

    Args:
        client: Anthropic client
        lead: Complete lead dict with company, industry_engagement, qualification, decision-maker
        model: Anthropic model ID to use

    Returns:
        Outreach dict with subject, message, status
    """
    # Extract relevant data
    company_name = lead['company']['name']
    company_description = lead['company']['description']
    industry_engagement = lead.get('industry_engagement', {})
    engagement_summary = industry_engagement.get('summary', 'Active in the graphics and signage industry')
    engagement_confidence = industry_engagement.get('confidence', 'inferred')
    decision_maker_name = lead['decision_maker']['name']
    decision_maker_title = lead['decision_maker']['title']
    qualification_score = lead['qualification'].get('weighted_total', 0)
    competitor_flag = lead['company'].get('competitor_flag', False)

    prompt = f"""You are drafting a personalized B2B outreach email for DuPont Tedlar to a potential customer in the graphics and signage industry.

**DuPont Tedlar Value Proposition:**
Tedlar produces protective PVF (polyvinylidene fluoride) films for graphics and signage applications. Key benefits:
- Exceptional durability and weather resistance
- UV protection extending graphic life 12-20+ years
- Ideal for large-format graphics, vehicle wraps, architectural applications
- Protective overlaminate for durable signage

**Lead Information:**
- Company: {company_name}
- Decision-Maker: {decision_maker_name}, {decision_maker_title}
- Business: {company_description}
- Industry Engagement: {engagement_summary}
- Engagement Confidence: {engagement_confidence} (confirmed = 2026 event attendance, historical = past event attendance, inferred = likely participant based on ICP)
- Fit Score: {qualification_score}/100
- Competitor Flag: {competitor_flag}

**Guidelines:**
1. Professional, concise, warm tone - NOT generic or overly salesy
2. Reference their industry engagement context naturally (e.g., if they attend ISA, mention it; if inferred, focus on their industry focus)
3. Connect Tedlar's value prop to their specific business focus
4. If competitor_flag is True, acknowledge potential overlap and focus on non-competing product lines or partnership opportunities
5. Clear, non-pushy CTA (e.g., "Would a 15-minute intro call make sense?")
6. Keep email body to 100-150 words

**Output Format (JSON):**
{{
  "subject": "Email subject line (specific, not generic)",
  "message": "Email body text (include greeting with first name, body, and signature)"
}}

Draft the outreach now."""

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

            return {
                "subject": data.get('subject', 'DuPont Tedlar Partnership Opportunity'),
                "message": data.get('message', ''),
                "status": "draft"
            }
        else:
            raise ValueError("No JSON found in outreach response")

    except Exception as e:
        raise Exception(f"Failed to draft outreach: {e}")


if __name__ == "__main__":
    # Test outreach agent
    test_leads = [
        {
            "event": {"name": "ISA Sign Expo 2026", "date": "April 2026"},
            "company": {
                "name": "Test Company",
                "description": "Large-format signage manufacturer",
                "competitor_flag": False
            },
            "qualification": {"weighted_total": 85, "label": "High"},
            "decision_maker": {
                "name": "John Doe",
                "title": "VP Product Development"
            }
        }
    ]
    results = run_outreach(test_leads)
    print(f"\nDrafted outreach for {len(results)} leads")
