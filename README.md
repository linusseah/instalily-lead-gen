# Instalily — AI-Powered Lead Generation Pipeline

> **Case Study:** DuPont Tedlar Graphics & Signage Lead Intelligence System

A working prototype of an autonomous AI agent system that researches industry events, identifies qualified companies, scores them against a structured ICP rubric, finds decision-makers, and drafts personalized outreach — all presented in an interactive Streamlit dashboard.

---

## Overview

This project demonstrates a practical, production-ready approach to AI-powered B2B lead generation. Using **Exa API** for semantic research and **Claude API** with web search for enrichment and qualification, the system autonomously processes leads from initial research through to personalized outreach drafts.

### Key Features

- **Fully Autonomous Pipeline** — Run once via `python main.py`, no human intervention during processing
- **Real Data Sources** — Exa API pulls live event and company data; Claude web search enriches with current information
- **Structured Qualification** — 4-criterion ICP rubric with weighted scoring (0-100) and High/Medium/Low labels
- **Personalized Outreach** — Context-aware email drafts referencing event presence and company-specific value props
- **Interactive Dashboard** — Streamlit UI for reviewing, filtering, and managing leads
- **Integration-Ready** — Documented stubs for Clay API and LinkedIn Sales Navigator showing production pathway

---

## Architecture

### Three-Agent Sequential Pipeline

```
python main.py
    │
    ▼
[1] Research Agent          ← Exa API (semantic search)
    │ events + companies
    ▼
[2] Enrichment Agent        ← Claude API with web_search
    │   Phase A: Company enrichment (revenue, size, strategic fit)
    │   Phase B: Qualification scoring (4-criterion rubric → score → label)
    │ enriched + scored lead profiles
    ▼
[3] Outreach Agent          ← Claude API (no web search)
    │ personalized outreach messages per decision-maker
    ▼
data/leads.json             ← flat file storage
    │
    ▼
Streamlit Dashboard         ← reads leads.json, displays to user
```

**Design Philosophy:** Simple chained Python functions calling APIs and passing structured JSON. Not using Claude Agent SDK — deliberate choice for predictability and debuggability within a rapid prototype window.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Exa API key ([get one here](https://exa.ai/))

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/instalily-lead-gen.git
cd instalily-lead-gen
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env and add your API keys:
# ANTHROPIC_API_KEY=your_key_here
# EXA_API_KEY=your_key_here
```

### Running the Pipeline

**Step 1: Run the pipeline**

```bash
python main.py
```

This will:
- Search for relevant industry events and companies (Research Agent)
- Enrich company data and score against ICP rubric (Enrichment Agent)
- Draft personalized outreach for each decision-maker (Outreach Agent)
- Save results to `data/leads.json`

Expected runtime: 5-15 minutes depending on number of companies found.

**Step 2: Launch the dashboard**

```bash
streamlit run dashboard/app.py
```

Open your browser to `http://localhost:8501` to view and manage leads.

---

## Agent Details

### Agent 1: Research Agent

**Purpose:** Find relevant trade shows and exhibiting companies

**Tool:** Exa API (semantic search)

**Queries:**
- `"ISA Sign Expo exhibitors signage companies"`
- `"large format printing industry associations exhibitors"`
- `"vehicle wrap architectural graphics exhibitions companies"`

**Output:** Events (name, date, location, relevance) + Companies (name, website, initial fit signal)

### Agent 2: Enrichment Agent

**Purpose:** Enrich and qualify companies (two internal phases)

**Tool:** Claude API with `web_search_20250305`

**Phase A — Company Enrichment:**
- Revenue / company size estimate
- Core business description
- Strategic fit rationale
- Key decision-maker identification (name, title, LinkedIn)

**Phase B — Qualification Scoring:**

Scores each company on 4 criteria (0-10 each):

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Industry Fit** | 30% | Core business in large-format signage, vehicle wraps, fleet graphics, or architectural graphics |
| **Size & Revenue** | 20% | Revenue >$50M or 200+ employees preferred |
| **Strategic Relevance** | 30% | Use/produce protective overlaminates or durable graphic films for Tedlar supply |
| **Event Engagement** | 20% | Active participation in ISA, PRINTING United, FESPA, SEGD |

**Score Calculation:**
```
weighted_total = (industry_fit × 0.30 + size × 0.20 + strategic_relevance × 0.30 + event_engagement × 0.20) × 10
```

**Labels:**
- ≥70 → "High"
- 40-69 → "Medium"
- <40 → "Low"

### Agent 3: Outreach Agent

**Purpose:** Draft personalized outreach emails

**Tool:** Claude API (no web search needed)

**Approach:**
- References specific event presence
- Connects Tedlar value prop to company's focus area
- Includes clear, non-pushy CTA
- Professional, concise, warm tone (100-150 words)

**Output:** Subject line + email body

---

## Dashboard Features

### Section 1: Summary Metrics
- Total Leads
- High Fit Leads
- Outreach Drafted
- Events Covered

### Section 2: Sidebar Filters
- Filter by Event (multi-select)
- Filter by Fit Score (High/Medium/Low)
- Toggle: Show/Hide integration stubs
- Download filtered leads as CSV

### Section 3: Lead Table + Expandable Cards
- **Table view:** Event, Company, Revenue, Fit Score, Decision-Maker, Status
- **Expanded view:** Full qualification breakdown, decision-maker details, outreach message with copy-to-clipboard
- **Status management:** Mark leads as Draft → Reviewed → Sent

---

## Integration Stubs

This prototype includes **documented stubs** for two key integrations that would be activated in production:

### 1. Clay API (`integrations/clay_stub.py`)
**Purpose:** Waterfall enrichment across 50+ data sources for verified contact details

**Provides:**
- Verified email addresses
- Phone numbers
- LinkedIn profile matching
- High-confidence contact discovery

**To activate:** See detailed instructions in `integrations/clay_stub.py`

### 2. LinkedIn Sales Navigator API (`integrations/linkedin_stub.py`)
**Purpose:** Decision-maker discovery and profile verification

**Provides:**
- Advanced people search by company and title
- Profile data including connections and shared experiences
- InMail messaging capabilities

**To activate:** See detailed instructions in `integrations/linkedin_stub.py`

---

## Data Schema

Output is saved to `data/leads.json` in the following structure:

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
        "relevance": "Largest sign and graphics industry trade show..."
      },
      "company": {
        "name": "Company Name",
        "website": "https://example.com",
        "revenue_estimate": "$50M-100M",
        "size": "200-500 employees",
        "description": "Company description...",
        "competitor_flag": false,
        "enrichment_status": "success"
      },
      "qualification": {
        "scores": {
          "industry_fit": 8,
          "size_and_revenue": 7,
          "strategic_relevance": 9,
          "event_engagement": 6
        },
        "weighted_total": 78,
        "label": "High",
        "rationale": "Strong fit for Tedlar's protective film applications..."
      },
      "decision_maker": {
        "name": "Jane Doe",
        "title": "VP Product Development",
        "linkedin": "https://linkedin.com/in/janedoe",
        "source": "web_search",
        "email": null,
        "phone": null
      },
      "outreach": {
        "subject": "DuPont Tedlar x Company Name — Protective Films Partnership",
        "message": "Hi Jane, I noticed...",
        "status": "draft"
      }
    }
  ]
}
```

---

## Error Handling

The pipeline implements robust error handling:

- **Per-lead try/except:** Pipeline continues if individual leads fail
- **Graceful degradation:** Failed enrichment → skip qualification, continue to next lead
- **Status tracking:** `enrichment_status`, `qualification.label`, `outreach.status` fields track success/failure
- **Dashboard resilience:** Handles null/missing fields without crashing

---

## Scalability & Production Roadmap

This prototype is intentionally simple for rapid development. Production evolution path:

1. **Parallelization** — `asyncio` for concurrent enrichment across multiple companies
2. **Database** — Replace JSON with Supabase for proper lead tracking and history
3. **Live Integrations** — Activate Clay + LinkedIn stubs for verified contact data
4. **Parameterized ICP** — Replace hardcoded Tedlar ICP with structured input schema for any client
5. **Scheduled Runs** — GitHub Actions cron job for weekly automated pipeline execution
6. **Webhooks** — Slack notifications when new leads are ready for review
7. **Frontend Upgrade** — React dashboard (via Lovable or similar) deployed on Vercel
8. **Agent Evaluation** — RLHF loop to improve qualification accuracy over time

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Language | Python 3.11+ | Core implementation |
| Research | Exa API | Semantic search for events and companies |
| Enrichment | Anthropic Claude API | Company enrichment + qualification with web search |
| Outreach | Anthropic Claude API | Personalized message drafting |
| Storage | JSON flat file | Simple, inspectable, version-controllable |
| Dashboard | Streamlit | Rapid prototyping, good demo UX |
| Future: Contact Data | Clay API (stub) | Waterfall contact enrichment |
| Future: LinkedIn | Sales Navigator (stub) | Decision-maker verification |

---

## Project Structure

```
instalily-lead-gen/
├── agents/
│   ├── research_agent.py       # Exa API — events + companies
│   ├── enrichment_agent.py     # Claude API — enrich + qualify (2 phases)
│   └── outreach_agent.py       # Claude API — personalized outreach
├── integrations/
│   ├── exa_client.py           # Exa API wrapper
│   ├── clay_stub.py            # Clay API stub (documented, not live)
│   └── linkedin_stub.py        # LinkedIn Sales Navigator stub
├── data/
│   └── leads.json              # Pipeline output (generated)
├── dashboard/
│   └── app.py                  # Streamlit dashboard
├── main.py                     # Orchestrator — runs all 3 agents
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── CLAUDE.md                   # Master project brief
└── README.md                   # This file
```

---

## Use Case: DuPont Tedlar

**ICP Overview:**

DuPont Tedlar manufactures protective PVF films for graphics and signage applications with exceptional durability, weather resistance, and UV protection (12-20+ year graphic life).

**Target Industries:**
- Large-format signage
- Vehicle wraps and fleet graphics
- Architectural graphics
- Protective overlaminates for durable signage

**Target Events:**
- ISA Sign Expo (April 2026, Orlando)
- PRINTING United Expo (September 2026, Las Vegas)
- FESPA Global Print Expo (May 2026, Barcelona)
- SEGD conferences

**Example Qualified Company:** Avery Dennison Graphics Solutions
- Specializes in large-format signage, vehicle wraps, architectural graphics
- $8B+ revenue, global scale
- Active at ISA Sign Expo
- Note: Also a competitor in some overlaminate categories — flagged accordingly

---

## Development Notes

### Key Design Decisions

| Decision | Resolution |
|----------|------------|
| Agent count | 3 agent files; Enrichment Agent has 2 internal phases |
| Qualification approach | Numerical rubric (4 criteria × 10) → weighted total → High/Medium/Low label |
| Dashboard layout | Summary metrics → filterable table → expandable detail cards |
| Contact info | Null in prototype; stubs point to Clay/LinkedIn for production |
| Competitor handling | Flag with `competitor_flag: true`, include in leads with note |

### Testing Individual Agents

Each agent file can be run standalone for testing:

```bash
python agents/research_agent.py
python agents/enrichment_agent.py
python agents/outreach_agent.py
```

Integration stubs also have test harnesses:

```bash
python integrations/clay_stub.py
python integrations/linkedin_stub.py
```

---

## Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Connect your GitHub account
4. Deploy from `dashboard/app.py`
5. Add environment variables in Streamlit dashboard settings (if needed for live API calls)

The dashboard reads from `data/leads.json` — commit a sample file or run the pipeline locally and commit the results.

---

## Contributing

This is a case study prototype. For production use cases or contributions, please:

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request with detailed description

---

## License

MIT License — See LICENSE file for details

---

## Contact & Support

For questions, issues, or feedback:
- Open an issue on GitHub
- Contact: [your-email@example.com]

---

**Built with Claude Code by Anthropic**

*This project demonstrates practical AI agent architecture for B2B lead generation — autonomous, scalable, and production-ready.*
