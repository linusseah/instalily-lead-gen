# Instalily Case Study — Master Project Brief for Claude Code

> **This is the single source of truth.** All prior discussion threads have been reconciled here.
> Last updated: 2026-03-11

---

## What We're Building

A working prototype of an AI-powered lead generation and enrichment pipeline for Instalily, using DuPont Tedlar's Graphics & Signage team as the test case. The system autonomously researches industry events, identifies qualified companies, scores them against a structured ICP rubric, finds decision-makers, and drafts personalized outreach — all presented in a Streamlit dashboard.

---

## End-to-End User Flow

1. **Pipeline runs once** via `python main.py` — no human intervention during processing
2. **Sales rep opens Streamlit dashboard** — hosted on Streamlit Community Cloud
3. **Rep scans the lead table** — filtered by event, fit score, or status
4. **Rep expands a lead card** — sees full qualification breakdown, decision-maker detail, and outreach draft
5. **One-click action** — copy outreach message to clipboard or mark as reviewed/sent

The human-in-the-loop moment is at the END. Agents run fully autonomously; humans review outputs.

---

## Architecture — Three Agent Pipeline (Sequential, Deterministic)

**NOT using the Claude Agent SDK.** Uses simple chained Python functions, each calling the Claude API or Exa API, passing structured output to the next step. Deliberate choice for predictability and debuggability within a 72-hour build window.

```
python main.py
    │
    ▼
research_agent()          ← Exa API (semantic search)
    │ events + companies
    ▼
enrichment_agent()        ← Claude API with web_search tool
    │   Phase A: Company enrichment (revenue, size, strategic fit)
    │   Phase B: Qualification scoring (4-criterion rubric → score → label)
    │ enriched + scored lead profiles
    ▼
outreach_agent()          ← Claude API (no web search needed)
    │ personalized outreach messages per decision-maker
    ▼
data/leads.json           ← flat file storage
    │
    ▼
Streamlit Dashboard       ← reads leads.json, displays to user
```

> **Presentation framing:** In documentation and slides, describe this as 3 agents where Agent 2 (Enrichment Agent) has two internal phases — enrichment and qualification. Narrate it as: "qualification is tightly coupled to enrichment because you need the enriched data to score the lead, so we designed them as a single agent step." This is architecturally sound and honest to the code.

---

## Agent Responsibilities

### Agent 1 — Research Agent (`agents/research_agent.py`)
- **Tool:** Exa API (semantic search)
- **Goal:** Find relevant trade shows, associations, and industry events for the graphics & signage industry where DuPont Tedlar's ICP will be present. Then, for each event, find exhibiting or attending companies that match the Tedlar ICP.
- **Example Exa queries:**
  - `"graphics and signage industry trade shows 2025 2026"`
  - `"large format printing industry associations exhibitors"`
  - `"vehicle wrap architectural graphics exhibitions companies"`
  - `"ISA Sign Expo exhibitors signage companies"`
  - `"PRINTING United Expo large format exhibitors"`
- **Output:** List of events (name, date, location, relevance rationale) + list of candidate companies per event (name, website, initial fit signal)

### Agent 2 — Enrichment Agent (`agents/enrichment_agent.py`)
- **Tool:** Claude API with `web_search_20250305` tool enabled
- **Two internal phases:**

  **Phase A — Company Enrichment**
  - Revenue / company size estimate (from public data)
  - Core business description
  - Strategic fit rationale against Tedlar ICP
  - Key decision-maker identification (name, title, LinkedIn URL where findable)

  **Phase B — Qualification Scoring (rubric)**
  Score each company against 4 criteria, 0–10 each:

  | Criterion | Weight | What to score |
  |-----------|--------|---------------|
  | Industry Fit | 30% | Is core business in large-format signage, vehicle wraps, fleet graphics, or architectural graphics? |
  | Size & Revenue | 20% | Revenue >$50M or 200+ employees preferred. Scale score accordingly. |
  | Strategic Relevance | 30% | Do they use, specify, or produce protective overlaminates / durable graphic films that Tedlar could supply? |
  | Event & Association Engagement | 20% | Do they exhibit at or actively participate in ISA, PRINTING United, FESPA, SEGD? |

  **Score calculation:**
  - Weighted total = (industry_fit × 0.30 + size × 0.20 + strategic_relevance × 0.30 + event_engagement × 0.20) × 10
  - Result = score out of 100
  - Label mapping: ≥70 → "High", 40–69 → "Medium", <40 → "Low"
  - Include a 1–2 sentence qualitative rationale summarising the score

- **ICP Reference Criteria:**
  - Industry fit: large-format signage, vehicle wraps, fleet graphics, architectural graphics
  - Size: preference for established companies with procurement processes
  - Strategic relevance: overlap with Tedlar's protective film / UV-resistant overlaminate value proposition
  - Industry engagement: active in key trade shows and associations
  - Market activity: expanding into durable, weather-resistant graphic films

- **Competitor flag:** Avery Dennison and 3M are Tedlar competitors — flag these with `"competitor_flag": true` and note this in the rationale. They can still be leads (for different product lines) but should be clearly marked.

### Agent 3 — Outreach Agent (`agents/outreach_agent.py`)
- **Tool:** Claude API (no web search needed — works from enriched data in leads.json)
- **Goal:** For each qualified decision-maker, draft a personalized outreach message that references:
  - Their specific event presence (where they were found)
  - Their company's core focus area
  - A specific Tedlar value proposition relevant to their use case
  - A clear, non-pushy call to action (e.g. "Would a 15-minute intro call make sense?")
- **Tone:** Professional, concise, warm — not generic, not salesy
- **Output:** Subject line + email body (~100–150 words)

---

## DuPont Tedlar ICP Reference

Use this throughout the pipeline to qualify companies. This is the ground truth for what a good lead looks like.

**Tedlar's value proposition:** Protective PVF films for graphics and signage applications — durability, weather resistance, UV protection, and extended graphic life (12–20+ years) for large-format graphics, vehicle wraps, and architectural applications.

**Example qualified company: Avery Dennison Graphics Solutions**
- Specialises in large-format signage, vehicle wraps, architectural graphics
- $8B+ revenue, thousands of employees globally
- Exhibits at ISA Sign Expo, active in relevant industry associations
- Expanding into durable, weather-resistant graphic films
- Example decision-maker: Laura Noll — https://www.linkedin.com/in/laura-noll-6388a55/
- Note: Also a competitor in some overlaminate categories — flag accordingly

**Key events to research:**
- ISA Sign Expo (April 2026, Orlando — DuPont joined ISA in 2025)
- PRINTING United Expo (Sept 2026, Las Vegas)
- FESPA Global Print Expo (May 2026, Barcelona)
- SEGD (Society for Experiential Graphic Design) events

**Key associations:**
- International Sign Association (ISA)
- PRINTING United Alliance
- FESPA
- SEGD

---

## Data Storage

Flat JSON file `data/leads.json`. Extended schema below — note the qualification block with full score breakdown.

```json
{
  "generated_at": "2026-03-11T10:00:00",
  "pipeline_version": "1.0.0",
  "leads": [
    {
      "event": {
        "name": "ISA Sign Expo 2026",
        "date": "April 2026",
        "location": "Orlando, FL",
        "relevance": "Largest sign and graphics industry trade show in North America. DuPont joined ISA in 2025."
      },
      "company": {
        "name": "Avery Dennison Graphics Solutions",
        "website": "https://www.averydennison.com",
        "revenue_estimate": "$8B+",
        "size": "10,000+ employees",
        "description": "Global leader in pressure-sensitive materials and graphic solutions including large-format signage, vehicle wraps, and architectural graphics.",
        "competitor_flag": true,
        "enrichment_status": "success"
      },
      "qualification": {
        "scores": {
          "industry_fit": 9,
          "size_and_revenue": 10,
          "strategic_relevance": 8,
          "event_engagement": 9
        },
        "weighted_total": 88,
        "label": "High",
        "rationale": "Core business is squarely within Tedlar's ICP — large-format graphics, vehicle wraps, and architectural applications. Global scale indicates established procurement. Note: also a competitor in overlaminate category; outreach should be scoped to non-competing product lines."
      },
      "decision_maker": {
        "name": "Laura Noll",
        "title": "VP Product Development",
        "linkedin": "https://www.linkedin.com/in/laura-noll-6388a55/",
        "source": "web_search",
        "email": null,
        "phone": null,
        "clay_stub": "STUB: Clay API would waterfall-enrich contact details across 50+ data sources here",
        "linkedin_stub": "STUB: LinkedIn Sales Navigator API would verify contact and pull email/phone here"
      },
      "outreach": {
        "subject": "DuPont Tedlar x Avery Dennison — Protective Films for Graphics Durability",
        "message": "Hi Laura, I noticed Avery Dennison is exhibiting at ISA Sign Expo this April — congrats on the continued expansion into durable graphic films. I'm reaching out from DuPont Tedlar to explore whether there's a fit between Tedlar's PVF protective films and Avery Dennison's large-format and vehicle wrap product lines. Our films are spec'd by leading sign manufacturers to extend graphic life 12–20+ years. Would a 15-minute intro call make sense to explore potential alignment?",
        "status": "draft"
      }
    }
  ]
}
```

---

## Integration Stubs

These are NOT live integrations. They are documented stubs showing exactly where real integrations would slot in — and are a deliberate talking point in the presentation.

### Clay API Stub (`integrations/clay_stub.py`)

```python
def enrich_contact_clay(company_name: str, title: str) -> dict:
    """
    STUB: In production, this calls the Clay API to waterfall-enrich
    contact details across 50+ data sources (email, phone, LinkedIn, etc.).

    Clay API docs: https://clay.com/api
    Endpoint: POST /enrichment/contact
    Inputs: company_name, job_title
    Returns: {name, email, phone, linkedin_url, verified: bool, source: str}

    To activate:
    1. Add CLAY_API_KEY to .env
    2. Replace this stub with an HTTP call to Clay's enrichment endpoint
    3. Handle rate limits (Clay tier-dependent) and validation
    """
    return {
        "stub": True,
        "message": "Clay API integration pending — would return verified contact details",
        "inputs": {"company": company_name, "title": title}
    }
```

### LinkedIn Sales Navigator Stub (`integrations/linkedin_stub.py`)

```python
def find_decision_maker_linkedin(company_name: str, title: str) -> dict:
    """
    STUB: In production, this calls the LinkedIn Sales Navigator API
    to find, verify, and pull profile data for decision-makers.

    Requires: LinkedIn Sales Navigator API (enterprise tier)
    Endpoint: GET /salesNavigator/search/people
    Inputs: company_name, job_title_keywords
    Returns: {name, title, linkedin_url, connection_degree, mutual_connections}

    To activate:
    1. Obtain LinkedIn Sales Navigator API access (enterprise agreement required)
    2. Add LINKEDIN_API_KEY to .env
    3. Implement OAuth 2.0 flow
    4. Replace this stub with authenticated API call
    """
    return {
        "stub": True,
        "message": "LinkedIn Sales Navigator integration pending",
        "inputs": {"company": company_name, "title": title}
    }
```

---

## Streamlit Dashboard Requirements (`dashboard/app.py`)

### Layout — Three Sections

**Section 1: Header + Summary Metrics**
- Header: `"Instalily — DuPont Tedlar Lead Intelligence Dashboard"`
- Subheader: pipeline run timestamp + total leads generated
- 4 metric cards in a row:
  - Total Leads
  - High Fit Leads
  - Outreach Drafted
  - Events Covered

**Section 2: Sidebar Filters**
- Filter by Event (multi-select)
- Filter by Fit Score label (High / Medium / Low)
- Toggle: Show / Hide integration stubs
- Button: Download filtered leads as CSV

**Section 3: Lead Table (main content)**
- One row per lead, showing:
  - Event Name
  - Company Name
  - Revenue Estimate
  - Fit Score badge (color-coded: 🟢 High / 🟡 Medium / 🔴 Low)
  - Decision-Maker Name + Title
  - LinkedIn link (if available)
  - Outreach Status (Draft / Reviewed / Sent)
  - "Expand" button → opens detail card below the row

**Expanded Lead Card (on click):**
1. Event: name, date, location, relevance
2. Company: description, website, competitor flag (if applicable)
3. Qualification Breakdown:
   - Score bars or metric display for each of the 4 criteria
   - Weighted total score + label
   - Qualitative rationale
4. Decision-Maker: name, title, LinkedIn link, stub status indicator
5. Outreach Message: subject + body, with copy-to-clipboard button
6. Status toggle: Draft → Reviewed → Sent (updates leads.json)

---

## Repo Structure

```
instalily-lead-gen/
├── agents/
│   ├── research_agent.py       # Exa API — events + companies
│   ├── enrichment_agent.py     # Claude API — enrich + qualify (2 phases)
│   └── outreach_agent.py       # Claude API — personalized outreach drafts
├── integrations/
│   ├── exa_client.py           # Exa API wrapper
│   ├── clay_stub.py            # Clay API stub (documented, not live)
│   └── linkedin_stub.py        # LinkedIn Sales Navigator stub
├── data/
│   └── leads.json              # Pipeline output — read by dashboard
├── dashboard/
│   └── app.py                  # Streamlit dashboard
├── main.py                     # Orchestrator — runs all 3 agents in sequence
├── requirements.txt
├── .env.example
├── CLAUDE.md                   # This file — project brief for Claude Code
└── README.md
```

---

## Environment Variables (`.env.example`)

```
ANTHROPIC_API_KEY=your_key_here
EXA_API_KEY=your_key_here

# Future integrations (stubs only in current build):
# CLAY_API_KEY=your_key_here
# LINKEDIN_API_KEY=your_key_here
```

---

## Tech Stack

| Layer | Tool | Notes |
|-------|------|-------|
| Language | Python 3.11+ | |
| Research | Exa API (`exa-py`) | Semantic search for events + companies |
| Enrichment + Qualification | Anthropic API (`anthropic`) | With `web_search_20250305` tool |
| Outreach | Anthropic API (`anthropic`) | No web search needed |
| Storage | Flat JSON (`data/leads.json`) | Simple, inspectable, no DB needed |
| Frontend | Streamlit | Rapid dashboard, good for demo |
| Hosting | Streamlit Community Cloud | Deploy from GitHub, free tier |
| Stubs | Clay API, LinkedIn Sales Navigator | Documented integration points, not live |

---

## Error Handling Requirements

- Wrap all API calls in `try/except` — pipeline must not crash if one lead fails
- Log errors per lead and continue processing remaining leads
- If enrichment fails for a company: set `"enrichment_status": "failed"`, skip qualification + outreach, continue pipeline
- If qualification scoring fails: set `"label": "Unknown"`, include raw rationale if available
- If outreach draft fails: set `"status": "draft_failed"`, do not block dashboard rendering
- Dashboard must gracefully handle `null` or missing fields — show "Not available" not crash

---

## Scalability Narrative (for documentation — not built)

Current prototype is sequential and single-batch. Production evolution path:

1. **Parallelise agent calls** — `asyncio` for concurrent enrichment across multiple companies
2. **Replace JSON with Supabase** — proper database with lead status tracking and history
3. **Activate Clay + LinkedIn stubs** — live contact enrichment and verification
4. **Parameterise the ICP** — replace hardcoded DuPont Tedlar ICP with a structured input schema so any client's ICP can be plugged in
5. **Schedule pipeline** — GitHub Actions cron job, runs weekly automatically
6. **Add human-in-the-loop webhook** — Slack notification when new leads are ready for review
7. **Rebuild frontend in React** — via Lovable or similar, deployed on Vercel, accessible without Python environment
8. **Run evals on agent performance** — RLHF / fine-tuning loop to improve qualification accuracy over time

---

## Build Priority Order (72-hour window)

1. `main.py` orchestrator skeleton + data schema (`leads.json` structure)
2. `agents/research_agent.py` — Exa API working, events + companies populating `leads.json`
3. `agents/enrichment_agent.py` — Phase A (enrich) + Phase B (qualify with rubric)
4. `agents/outreach_agent.py` — Claude drafting outreach per decision-maker
5. `integrations/clay_stub.py` + `linkedin_stub.py` — documented stubs with clear activation instructions
6. `dashboard/app.py` — Streamlit dashboard: metrics → table → expandable cards
7. `README.md` + `.env.example` + deploy to Streamlit Community Cloud
8. Technical documentation PDF (3 pages max)
9. Presentation slides

---

## Evaluation Criteria Checklist (from brief)

- ✅ Uses real data effectively — Exa API pulls live event/company data; Claude web search enriches with real company info
- ✅ Automates lead processing with minimal manual intervention — single `python main.py` command runs full pipeline
- ✅ Handles errors and ensures clean structured outputs — try/except throughout, structured JSON with status flags
- ✅ Demonstrates scalable approach — documented in stubs, scalability narrative, and parameterised ICP design
- ✅ Personalised outreach — per decision-maker, referencing event context and company-specific value prop
- ✅ Integration design — Clay and LinkedIn Sales Navigator stubs with clear activation instructions

---

## Key Decisions — Resolved Conflicts Log

| Decision | Resolution |
|----------|------------|
| 3 vs 4 agents | 3 agent files; Enrichment Agent has 2 internal phases (enrich + qualify) |
| Qualification: qualitative vs numerical | Numerical rubric (4 criteria × 10, weighted total out of 100) → produces High/Medium/Low label shown in dashboard |
| Dashboard: cards vs table | Both — summary metrics → filterable table (scannable) → expandable card per lead (detailed) |
| Contact info (email/phone) | Null in prototype; explicit stub markers pointing to Clay/LinkedIn integrations |
| Competitor flagging | Flag Avery Dennison / 3M with `competitor_flag: true`; include in leads with note |
| Event column | Included as first field in both table and card — ties each lead to its source event |
