# Instalily — AI-Powered Lead Generation Pipeline

> **Case Study:** DuPont Tedlar Graphics & Signage Lead Intelligence System

A working prototype of an autonomous AI agent system that identifies ICP-matching companies, finds decision-makers, scores them against a structured rubric, builds industry engagement profiles, and drafts personalised outreach — all surfaced in a Next.js dashboard deployed on Vercel.

---

## Overview

This project demonstrates a practical, production-ready approach to AI-powered B2B lead generation. Using **Exa API** for ICP-similarity discovery and **Claude API** with web search for enrichment and qualification, the system autonomously processes leads from initial research through to personalised outreach drafts.

### Key Features

- **Fully Autonomous Pipeline** — Run once via `python main.py`, no human intervention during processing
- **ICP-Similarity Discovery** — Exa `find_similar()` seeded from reference company URLs; far more reliable than keyword or event-attendee search
- **4-Phase Enrichment** — Company data → contact discovery → industry engagement → qualification scoring, all in one agent step
- **3-Tier Industry Engagement** — Confirmed event attendance, historical attendance, or inferred from ICP profile; always populated, never null
- **Contact Fallback Chain** — Named DM with LinkedIn → named DM only → generic email → contact page; companies never discarded for lack of contact
- **Structured Qualification** — 4-criterion ICP rubric with weighted scoring (0–100) and High/Medium/Low labels
- **Personalised Outreach** — Context-aware email drafts referencing industry engagement and company-specific value props
- **Next.js Dashboard** — HubSpot-style sliding detail panel, inline CRM editing, filterable lead table — deployed on Vercel
- **Integration-Ready** — Documented stubs for Clay API and LinkedIn Sales Navigator showing production pathway

---

## Architecture

### Three-Agent Sequential Pipeline

```
python main.py
    │
    ▼
[1] Research Agent          ← Exa API (findSimilar + keyword search)
    │ clean list of company names + websites (15–25 companies)
    ▼
[2] Enrichment Agent        ← Claude API with web_search tool
    │   Phase A: Company enrichment (revenue, size, description)
    │   Phase B: Contact discovery (decision-makers, LinkedIn, fallback chain)
    │   Phase C: Industry engagement (3-tier: confirmed/historical/inferred)
    │   Phase D: Qualification scoring (4-criterion rubric → score → label)
    │ fully enriched + scored lead profiles
    ▼
[3] Outreach Agent          ← Claude API (no web search needed)
    │ personalised outreach messages per decision-maker
    ▼
Supabase `leads` table      ← pipeline writes rows; dashboard reads via API
    │                         (data/leads.json written as backup)
    ▼
Next.js Dashboard           ← reads from Supabase via /api/leads, displays to user
```

**Design Philosophy:** Simple chained Python functions calling APIs and passing structured JSON. Not using Claude Agent SDK — deliberate choice for predictability and debuggability within a rapid prototype window. Enrichment and qualification are tightly coupled (you need enriched data before you can score), so they live as a single agent with four internal phases.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key ([get one here](https://console.anthropic.com/))
- Exa API key ([get one here](https://exa.ai/))
- Supabase project ([set up free here](https://supabase.com)) — see `SUPABASE_SETUP.md`

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/instalily-lead-gen.git
cd instalily-lead-gen
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

```bash
cp .env.example .env
# Add your API keys to .env
```

4. **Set up Supabase** — follow `SUPABASE_SETUP.md` to create the database and get credentials.

### Running the Pipeline

**Step 1: Run the pipeline**

```bash
python main.py            # Full pipeline
python main.py --test     # Quick test (3 companies)
python main.py --limit 5  # Process 5 companies
```

This will:
- Discover ICP-matching companies via Exa similarity search (Research Agent)
- Enrich, find contacts, build industry engagement profiles, and score leads (Enrichment Agent)
- Draft personalised outreach for each decision-maker (Outreach Agent)
- Write results to Supabase and `data/leads.json` (backup)

Expected runtime: 5–15 minutes depending on number of companies found.

**Step 2: Launch the dashboard**

```bash
cd dashboard-nextjs
npm install
npm run dev
```

Open your browser to `http://localhost:3000`.

---

## Agent Details

### Agent 1: Research Agent (`agents/research_agent.py`)

**Purpose:** Produce a clean list of real company names and websites matching the Tedlar ICP.

**Tool:** Exa API — `exa.find_similar()` + `exa.search()`

**Strategy 1 — ICP Similarity Search (primary)**

Seeds from known reference company URLs. Finds semantically similar company websites — far more reliable than keyword-based discovery.

```python
reference_urls = [
    "https://www.averydennison.com/.../graphics-solutions",
    "https://www.orafal.com/en/products/vehicle-wraps/",
    "https://www.arlon.com/graphics-media/",
    "https://www.fdcgraphicfilms.com/",
    "https://www.3m.com/.../graphics-signage-us/",
]
```

**Strategy 2 — ICP Keyword Search (secondary)**

Direct ICP-aligned queries targeting company websites, not directories or aggregators.

**Company Extraction — Claude, not URL parsing**

Exa results are passed to Claude with explicit instructions to extract real company names and exclude directories, LinkedIn, news sites, and aggregators.

**Output:** 15–25 deduplicated `{company_name, website}` pairs.

---

### Agent 2: Enrichment Agent (`agents/enrichment_agent.py`)

**Purpose:** Fully enrich each candidate company across four sequential phases.

**Tool:** Claude API with `web_search_20250305`

**Phase A — Company Enrichment**
- Revenue estimate and employee count
- Core business description (1–2 sentences)
- Primary product/service lines relevant to Tedlar ICP
- Sets `enrichment_status: "success"` or `"failed"` — failures skip Phases B/C/D

**Phase B — Contact Discovery**

Searches for decision-makers in priority order: Head of Partnerships → VP/Director of Procurement → VP/Director of Product → CEO/COO (small companies) → R&D Director.

Fallback chain (stops at first success):
1. Named DM + LinkedIn URL + email
2. Named DM + LinkedIn URL
3. Named DM + title only
4. Generic company email (info@, partnerships@)
5. Contact page URL
6. `contact_found: false` — company is kept, not discarded

Multiple contacts per company are allowed and stored in `additional_decision_makers`.

**Phase C — Industry Engagement Enrichment**

Builds an `industry_engagement` profile for every company. Always populated — never null.

| Tier | Label | How determined |
|------|-------|----------------|
| 1 | **Confirmed** | 2026 press release, blog post, or official exhibitor list |
| 2 | **Historical** | 2024/2025 attendance records found |
| 3 | **Inferred** | ICP profile strongly suggests relevant shows |

Target shows: ISA Sign Expo (April 2026, Orlando), PRINTING United Expo (Sept 2026, Las Vegas), FESPA Global Print Expo (May 2026, Barcelona), SEGD conference.

**Phase D — Qualification Scoring**

| Criterion | Weight | What it scores |
|-----------|--------|----------------|
| Industry Fit | 30% | Core business in large-format signage, vehicle wraps, fleet graphics, architectural graphics |
| Size & Revenue | 20% | Revenue >$50M or 200+ employees; scaled proportionally for smaller companies |
| Strategic Relevance | 30% | Uses or produces protective overlaminates / durable graphic films Tedlar could supply |
| Event Engagement | 20% | Active at ISA, PRINTING United, FESPA, or SEGD (from Phase C + general knowledge) |

Score: `(industry_fit × 0.30 + size × 0.20 + strategic_relevance × 0.30 + event_engagement × 0.20) × 10` → out of 100

Labels: ≥70 → **High**, 40–69 → **Medium**, <40 → **Low**

Competitor flag: Avery Dennison and 3M are flagged `competitor_flag: true` but included as leads — they may be targets for different product lines.

---

### Agent 3: Outreach Agent (`agents/outreach_agent.py`)

**Purpose:** Draft personalised outreach emails from enriched lead data.

**Tool:** Claude API (no web search — works entirely from enriched data)

Each message references:
- The decision-maker's specific role and company focus
- A Tedlar value proposition relevant to their use case
- Industry engagement context from Phase C (makes outreach warm and timely)
- A non-pushy CTA ("Would a 15-minute intro call make sense?")

**Output:** Subject line + ~100–150 word email body per lead. For companies with no named DM, addressed to "the Partnerships team".

---

## Dashboard

Built with **Next.js 14 App Router**, TypeScript, Tailwind CSS, and shadcn/ui. Deployed on Vercel.

### Layout

**Row 1 — Summary metrics:** Total Leads · High Fit · Open · In Progress

**Row 2 — Filterable lead table (13 columns):**
- Company, Decision-Maker, Title, Revenue, Size, Industry, Fit Score, Status, Owner, Event Engagement, Created Date, Last Interaction, Actions
- Sortable columns; inline-editable Status and Owner
- Filter by fit score, lead status, lead owner

**Row 3 — Sliding detail panel (HubSpot-style, opens on row click):**
- Contact Information (email, phone, LinkedIn with copy buttons)
- Company Information (name, website, revenue, size, description, competitor badge)
- Qualification Score Breakdown (progress bars per criterion + rationale)
- Industry Engagement (confidence badge: Confirmed/Historical/Inferred + summary text)
- Recommended Outreach (subject + message + copy-to-clipboard)
- CRM Data (editable: status, owner, last interaction date, notes + save)

### Data Flow

```
Supabase `leads` table
    ↓
Next.js /api/leads (GET / PATCH)
    ↓
Dashboard UI (reads + updates)
```

CRM edits (status, owner, notes, dates) write back to Supabase via PATCH. Optimistic UI updates — state updates immediately without waiting for the API response.

---

## Integration Stubs

Two production integrations are documented as stubs:

### Clay API (`integrations/clay_stub.py`)
Waterfall enrichment across 50+ data sources for verified emails, phones, and LinkedIn profiles. Directly addresses the Phase B contact discovery gap — web search finds ~60% of contacts; Clay fills the remaining 40% and verifies what was found.

### LinkedIn Sales Navigator (`integrations/linkedin_stub.py`)
Advanced people search by company and title; confirms job titles are current; surfaces mutual connections for outreach personalisation.

Both stubs include activation instructions and are surfaced in the dashboard detail panel.

---

## Data Schema

Pipeline writes to Supabase `leads` table. `data/leads.json` is a local backup only.

Key fields:

```
company_name, company_website, company_revenue_estimate, company_size,
company_description, competitor_flag, enrichment_status, contact_found

industry_engagement      -- always populated; human-readable summary
engagement_confidence    -- 'confirmed' | 'historical' | 'inferred'

score_industry_fit, score_size_revenue, score_strategic_relevance,
score_event_engagement, qualification_total, qualification_label,
qualification_rationale

dm_name, dm_title, dm_linkedin, dm_email, dm_phone, dm_source,
dm_contact_fallback, additional_decision_makers (JSONB)

outreach_subject, outreach_message, outreach_status

crm_lead_status, crm_lead_owner, crm_last_interaction_date, crm_notes
```

Full SQL schema in `supabase/schema.sql`.

---

## Deployment

### Deploy to Vercel

1. Push repo to GitHub
2. Import project at [vercel.com/new](https://vercel.com/new)
3. Set root directory to `dashboard-nextjs`
4. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. Deploy

The pipeline (`main.py`) runs locally or via GitHub Actions — not on Vercel. Vercel only serves the Next.js dashboard.

### Scheduled Pipeline Runs (GitHub Actions)

For automated weekly lead refreshes, add a GitHub Actions workflow that runs `python main.py` on a cron schedule and writes results to Supabase. This is a stateless batch job — no persistent server needed.

---

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Language | Python 3.11+ | Pipeline implementation |
| Research | Exa API | ICP-similarity search (`find_similar`) + keyword search |
| Enrichment | Anthropic Claude API | Company enrichment, contact discovery, industry engagement, qualification (with web search) |
| Outreach | Anthropic Claude API | Personalised message drafting |
| Database | Supabase (Postgres) | Primary data store; dashboard reads/writes here |
| Backup | JSON flat file | `data/leads.json` — local backup per pipeline run |
| Dashboard | Next.js 14 + Tailwind + shadcn/ui | Interactive lead management UI |
| Deployment | Vercel | Dashboard hosting (serverless) |
| Future: Contact Data | Clay API (stub) | Waterfall contact enrichment |
| Future: LinkedIn | Sales Navigator (stub) | Decision-maker verification |

---

## Project Structure

```
instalily-lead-gen/
├── agents/
│   ├── research_agent.py       # Exa findSimilar + keyword → Claude extraction
│   ├── enrichment_agent.py     # 4 phases: enrich, contacts, industry engagement, score
│   └── outreach_agent.py       # Claude API — personalised outreach
├── integrations/
│   ├── exa_client.py           # Exa API wrapper
│   ├── supabase_client.py      # Supabase read/write wrapper
│   ├── clay_stub.py            # Clay API stub (documented, not live)
│   └── linkedin_stub.py        # LinkedIn Sales Navigator stub
├── data/
│   └── leads.json              # Local backup — Supabase is source of truth
├── dashboard-nextjs/
│   ├── app/
│   │   ├── page.tsx            # Main dashboard page
│   │   └── api/leads/route.ts  # GET + PATCH API routes (reads/writes Supabase)
│   ├── components/
│   │   ├── LeadTable.tsx       # 13-column sortable table with inline editing
│   │   └── LeadDetailPanel.tsx # HubSpot-style sliding panel
│   ├── lib/
│   │   ├── types.ts            # TypeScript types (Lead, IndustryEngagement, etc.)
│   │   ├── supabase.ts         # Supabase JS client
│   │   └── utils.ts            # Formatting and utility functions
│   └── package.json
├── supabase/
│   └── schema.sql              # Run this in Supabase SQL Editor to set up tables
├── main.py                     # Orchestrator — runs all 3 agents
├── requirements.txt
├── .env.example
├── CLAUDE.md                   # Master project brief (single source of truth)
├── SUPABASE_SETUP.md           # Step-by-step Supabase setup guide
└── README.md
```

---

## Use Case: DuPont Tedlar

**Product:** Protective PVF films for graphics and signage — exceptional durability, weather resistance, UV protection (12–20+ year graphic life).

**ICP:** Companies that use, specify, or produce protective overlaminates and durable graphic films for large-format applications — vehicle wraps, fleet graphics, architectural graphics, outdoor signage.

**Reference companies used as discovery seeds:**
- Avery Dennison Graphics Solutions — $8B+ revenue; also a competitor, flagged
- Orafal Americas — pressure-sensitive adhesive films, vehicle wraps
- Arlon Graphics — high-performance graphics films and overlaminates
- FDC Graphic Films — distributor of graphic films and overlaminates
- 3M Commercial Graphics — large-format graphics, vehicle wraps; also a competitor, flagged

---

## Scalability Roadmap

1. **Parallelise enrichment** — `asyncio` for concurrent Phase A/B/C/D per company
2. **Activate Clay + LinkedIn stubs** — fills the contact discovery gap, verifies emails
3. **Parameterise the ICP** — replace hardcoded Tedlar config with JSON input schema for any client
4. **Schedule pipeline** — GitHub Actions cron → weekly automated refresh → Supabase
5. **Server-side filtering** — move filter logic into Supabase queries for scale
6. **Multi-tenant** — `client_id` column; reps see only their client's leads
7. **Evals + RLHF** — score qualification accuracy against rep feedback, improve over time

---

## Key Design Decisions

| Decision | Resolution |
|----------|------------|
| Primary discovery mechanism | ICP similarity search (Exa `findSimilar` seeded from reference URLs) — NOT event attendee lists |
| Events/conferences | Contextual enrichment only (Phase C) — not primary lead source |
| Company extraction | Claude parses Exa results — NOT URL domain extraction |
| Contact discovery | Phase B fallback chain; companies kept even with no named contact |
| Industry engagement | 3-tier model (confirmed/historical/inferred); always populated, never null |
| Agent count | 3 agents; Enrichment Agent has 4 internal phases |
| Data storage | Supabase Postgres (primary) + JSON backup |
| Dashboard | Next.js 14 App Router on Vercel; reads/writes Supabase |
| Competitor handling | `competitor_flag: true` on Avery Dennison / 3M; included with note |

---

*Built as a case study prototype demonstrating practical AI agent architecture for B2B lead generation.*
