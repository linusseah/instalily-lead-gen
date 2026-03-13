# Instalily Case Study — Master Project Brief for Claude Code

> **This is the single source of truth.** All prior discussion threads have been reconciled here.
> Last updated: 2026-03-13

---

## What We're Building

A working prototype of an AI-powered lead generation and enrichment pipeline for Instalily, using DuPont Tedlar's Graphics & Signage team as the test case. The system autonomously identifies companies that match the ICP, finds decision-makers, scores leads against a structured rubric, and drafts personalized outreach — all presented in a Next.js dashboard deployed on Vercel.

---

## End-to-End User Flow

1. **Pipeline runs once** via `python main.py` — no human intervention during processing
2. **Sales rep opens Next.js dashboard** — deployed on Vercel
3. **Rep scans the lead table** — filtered by fit score, status, or owner
4. **Rep expands a lead** — sees full qualification breakdown, decision-maker detail, event context, and outreach draft
5. **One-click action** — copy outreach message to clipboard or mark as reviewed/sent

The human-in-the-loop moment is at the END. Agents run fully autonomously; humans review outputs.

---

## Architecture — Three Agent Pipeline (Sequential, Deterministic)

**NOT using the Claude Agent SDK.** Uses simple chained Python functions, each calling the Claude API or Exa API, passing structured output to the next step.

```
python main.py
    │
    ▼
research_agent()          ← Exa API (findSimilar + semantic search)
    │ clean list of company names + websites
    ▼
enrichment_agent()        ← Claude API with web_search tool
    │   Phase A: Company enrichment (revenue, size, description)
    │   Phase B: Contact discovery (decision-makers, LinkedIn, contact info)
    │   Phase C: Event enrichment (conference context — enrichment only)
    │   Phase D: Qualification scoring (4-criterion rubric → score → label)
    │ fully enriched + scored lead profiles
    ▼
outreach_agent()          ← Claude API (no web search needed)
    │ personalized outreach messages per decision-maker
    ▼
Supabase `leads` table    ← pipeline writes rows; dashboard reads via API
    │
    ▼
Next.js Dashboard         ← reads from Supabase via /api/leads, displays to user
```

> **Presentation framing:** 3 agents where Agent 2 (Enrichment Agent) has four internal phases. Narrative: "enrichment and qualification are tightly coupled — you need the enriched data before you can score, and you need contacts before you can personalise outreach, so we designed them as a single agent step with structured internal phases."

---

## ⚠️ Critical: What Was Broken and What Has Changed

### Research Agent — Fundamental Redesign Required

The previous research agent was broken at the root level. It searched for exhibitor lists and extracted company names from URL domains, producing results like "Expoattendeelist" and "Tpgtsn" instead of real companies. The entire `parse_company_from_result()` function and the event-attendee search strategy must be replaced.

**The old (broken) approach:** Find events → search for exhibitor lists → extract domain names as company names

**The new approach:** Start from ICP similarity → find companies that look like the reference company → use event attendance as contextual enrichment only, never as the primary discovery mechanism

### Events/Conferences — Role Has Changed

Events are no longer the primary discovery mechanism. They are **contextual enrichment data** added in Agent 2 Phase C. The research agent does not search for exhibitor lists. Instead, after finding companies, the enrichment agent checks whether those companies attend relevant industry events — which makes the outreach warmer and more timely, but is not how companies are sourced in the first place.

---

## Agent Responsibilities — Revised

### Agent 1 — Research Agent (`agents/research_agent.py`) — FULL REWRITE

- **Tool:** Exa API — specifically `exa.find_similar()` and `exa.search()`
- **Goal:** Produce a clean list of real company names and their actual websites that match the Tedlar ICP. Nothing else. No contacts, no enrichment, no events at this stage.

**Strategy 1 — ICP Similarity Search (primary, most reliable)**

Use Exa's `find_similar()` endpoint with the URLs of known reference companies. This finds semantically similar company websites — far more reliable than keyword search for company discovery.

Reference URLs to use:
```python
reference_urls = [
    "https://www.averydennison.com/en/us/products-and-solutions/graphics-solutions.html",
    "https://www.orafal.com/en/products/vehicle-wraps/",
    "https://www.arlon.com/graphics-media/",
    "https://www.fdcgraphicfilms.com/",
    "https://www.3m.com/3M/en_US/graphics-signage-us/",
]

for url in reference_urls:
    results = exa.find_similar(url, num_results=10, exclude_source_domain=True)
    # Extract company websites from results
```

**Strategy 2 — ICP Keyword Search (secondary, for discovery of less well-known players)**

Direct ICP-aligned queries that return company websites, not directories:
```python
icp_queries = [
    "large format signage manufacturer protective films overlaminates",
    "vehicle wrap film distributor graphics solutions",
    "fleet graphics company durable outdoor films",
    "architectural graphics firm UV resistant materials",
    "print service provider large format graphics films",
    "sign manufacturer protective overlaminate films",
]
```

**Company Extraction — use Claude, not URL parsing**

After Exa returns results, pass the result titles, URLs, and snippets to Claude with this instruction: "From these search results, extract only real company names and their websites. Exclude: news sites, industry blogs, LinkedIn, aggregator directories, trade show websites, ContactOut, people-search sites. Return a JSON list of {company_name, website}."

This replaces the broken `parse_company_from_result()` domain-extraction logic entirely.

**Output format:**
```python
[
    {"company_name": "Orafal Americas", "website": "https://www.orafal.com"},
    {"company_name": "Arlon Graphics", "website": "https://www.arlon.com"},
    ...
]
```

Target: 15–25 candidate companies. Deduplicate by domain. Remove any company whose website is a directory, LinkedIn page, or aggregator site.

---

### Agent 2 — Enrichment Agent (`agents/enrichment_agent.py`) — EXPANDED

- **Tool:** Claude API with `web_search_20250305` tool enabled
- **Four internal phases, run sequentially per company:**

**Phase A — Company Enrichment**
Search for and extract:
- Revenue estimate and employee count (from public data, Crunchbase, news)
- Core business description (1–2 sentences)
- Primary product/service lines relevant to Tedlar ICP
- `enrichment_status`: set to `"success"` or `"failed"`

If enrichment fails (no data found), set `enrichment_status: "failed"` and skip Phases B, C, D. Log the failure and continue to the next company.

**Phase B — Contact Discovery**

For each successfully enriched company, search for decision-makers. Target roles in priority order: Head of Partnerships, VP/Director of Procurement, VP/Director of Product, CEO/COO (for smaller companies), R&D Director.

Search strategies:
```
"{company_name} VP Procurement LinkedIn"
"{company_name} head of partnerships site:linkedin.com"
"{company_name} leadership team"
"{company_website}/about" or "{company_website}/team"
"{company_name} Director partnerships signage"
```

**Contact output priority (fallback chain — stop at first success):**
1. Named decision-maker + LinkedIn URL + email (best case)
2. Named decision-maker + LinkedIn URL (no email)
3. Named decision-maker + title only (no LinkedIn)
4. Generic company contact email (info@, partnerships@, contact@)
5. Company contact page URL (e.g. company.com/contact)
6. No contact found — keep the company, set `contact_found: false`, note this explicitly

It is acceptable and expected to have leads with no individual contact info. Do not discard companies because no contact was found. The fallback to generic email or contact page is a valid lead.

It is acceptable to include more than one contact per company if multiple strong matches are found (e.g. both a VP of Procurement and a Head of Partnerships). Include all in a `decision_makers` array.

**Phase C — Industry Engagement Enrichment (contextual only)**

For each company, build an `industry_engagement` profile describing their presence at relevant trade shows and associations. This is enrichment context for the outreach message — it is NOT a qualifying criterion and does NOT affect the score.

This field is **always populated** — never left null. Use the 3-tier confidence model below, falling through each tier until one produces output:

**Tier 1 — Confirmed** (`engagement_confidence: "confirmed"`)
Search for 2026 announcements: press releases, company blog posts, official exhibitor/speaker/sponsor lists.
```
"{company_name} ISA Sign Expo 2026 exhibitor"
"{company_name} PRINTING United 2026"
"{company_name} FESPA 2026 Barcelona"
"site:isa.org OR site:printingunited.com {company_name}"
```
Example output: `"Confirmed exhibitor at ISA Sign Expo 2026 (April, Orlando) — see company press release."`

**Tier 2 — Historical** (`engagement_confidence: "historical"`)
If no 2026 confirmation found, search for past attendance (2024/2025):
```
"{company_name} ISA Sign Expo 2024 OR 2025"
"{company_name} PRINTING United 2024 OR 2025 exhibitor"
"{company_name} FESPA exhibitor OR sponsor"
"ISA Sign Expo sponsors 2024 {company_name}"
```
Example output: `"Exhibited at ISA Sign Expo 2025; strong likelihood of returning based on past participation."`

**Tier 3 — Inferred** (`engagement_confidence: "inferred"`)
If no attendance record found, reason from the company's industry profile and ICP fit to produce a confident inference about which shows are relevant to them:
Example output: `"Exhibits at key trade shows including ISA Sign Expo and PRINTING United Alliance; active in large-format graphics and signage industry. ISA membership likely given product focus."`

The output field `industry_engagement` is a single human-readable sentence or two (not structured sub-fields). Always indicate which tier the confidence came from.

**Phase D — Qualification Scoring (ICP rubric)**

Score each company against 4 criteria, 0–10 each:

| Criterion | Weight | What to score |
|-----------|--------|---------------|
| Industry Fit | 30% | Core business in large-format signage, vehicle wraps, fleet graphics, or architectural graphics? |
| Size & Revenue | 20% | Revenue >$50M or 200+ employees? Scale score proportionally for smaller companies. |
| Strategic Relevance | 30% | Do they use, specify, or produce protective overlaminates / durable graphic films that Tedlar could supply? |
| Event & Association Engagement | 20% | Active at ISA, PRINTING United, FESPA, or SEGD? (Based on Phase C findings + general knowledge.) |

Score calculation:
- `weighted_total` = (industry_fit × 0.30 + size_revenue × 0.20 + strategic_relevance × 0.30 + event_engagement × 0.20) × 10
- Result out of 100
- Label: ≥70 → "High", 40–69 → "Medium", <40 → "Low"
- Include 1–2 sentence qualitative rationale

**Competitor flag:** If the company is Avery Dennison, 3M, or a known direct competitor in the overlaminate/protective film category, set `competitor_flag: true` and note in the rationale. Include them as leads — they may be targets for different product lines — but flag clearly.

---

### Agent 3 — Outreach Agent (`agents/outreach_agent.py`) — UNCHANGED

- **Tool:** Claude API (no web search needed — works from enriched data)
- **Goal:** For each lead with a named decision-maker, draft a personalized outreach message that references:
  - The decision-maker's specific role and company focus
  - A specific Tedlar value proposition relevant to their use case
  - Conference/event context **if available from Phase C** (makes outreach timely and warm)
  - A clear, non-pushy call to action ("Would a 15-minute intro call make sense?")
- **Tone:** Professional, concise, warm — not generic, not salesy
- **Length:** ~100–150 words
- **Output:** Subject line + email body

For companies with no named decision-maker (only generic email or contact page), still draft an outreach — address it to "the Partnerships team" or equivalent. Do not skip outreach just because no individual contact was found.

---

## DuPont Tedlar ICP Reference

**Tedlar's value proposition:** Protective PVF films — durability, weather resistance, UV protection, extended graphic life (12–20+ years) for large-format graphics, vehicle wraps, and architectural applications.

**Reference companies (use as seeds in Agent 1):**
- Avery Dennison Graphics Solutions — $8B+ revenue, ISA Sign Expo exhibitor, expanding into weather-resistant graphic films. Also a competitor — flag accordingly. Example DM: Laura Noll — https://www.linkedin.com/in/laura-noll-6388a55/
- Orafal Americas — pressure-sensitive adhesive films, vehicle wraps, architectural graphics
- Arlon Graphics — high-performance graphics films and overlaminates
- FDC Graphic Films — distributor of graphic films and overlaminates
- 3M Commercial Graphics — large-format graphics, vehicle wraps. Also a competitor — flag accordingly.

**Key events (for Phase C enrichment context only):**
- ISA Sign Expo (April 2026, Orlando)
- PRINTING United Expo (Sept 2026, Las Vegas)
- FESPA Global Print Expo (May 2026, Barcelona)
- SEGD annual conference

**Key associations:** ISA, PRINTING United Alliance, FESPA, SEGD

---

## Data Schema — Supabase `leads` Table

```sql
create table leads (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz default now(),
  pipeline_run_at timestamptz,

  -- Company (from Agent 1 + Agent 2 Phase A)
  company_name text not null,
  company_website text,
  company_revenue_estimate text,
  company_size text,
  company_description text,
  competitor_flag boolean default false,
  enrichment_status text default 'success',
  contact_found boolean default true,

  -- Industry engagement (from Agent 2 Phase C — enrichment only)
  industry_engagement text,         -- human-readable summary (always populated, never null)
  engagement_confidence text,       -- 'confirmed' | 'historical' | 'inferred'

  -- Qualification (from Agent 2 Phase D)
  score_industry_fit integer,
  score_size_revenue integer,
  score_strategic_relevance integer,
  score_event_engagement integer,
  qualification_total integer,
  qualification_label text,
  qualification_rationale text,

  -- Decision maker (from Agent 2 Phase B — primary contact)
  dm_name text,
  dm_title text,
  dm_linkedin text,
  dm_email text,
  dm_phone text,
  dm_source text,
  dm_contact_fallback text,   -- generic email or contact page URL if no named DM

  -- Additional contacts (JSONB for multiple DMs per company)
  additional_decision_makers jsonb,

  -- Outreach (from Agent 3)
  outreach_subject text,
  outreach_message text,
  outreach_status text default 'draft',

  -- CRM (editable by reps in dashboard)
  crm_lead_status text default 'Open',
  crm_lead_owner text,
  crm_last_interaction_date timestamptz,
  crm_notes text
);
```

---

## Integration Stubs (documented, not live)

### Clay API Stub (`integrations/clay_stub.py`)
```python
def enrich_contact_clay(company_name: str, title: str) -> dict:
    """
    STUB: In production, calls Clay API to waterfall-enrich contact details
    across 50+ data sources (email, phone, LinkedIn, verified).

    This directly addresses the gap in Phase B contact discovery:
    web search finds ~60% of contacts; Clay fills the remaining 40%
    and verifies what was found.

    To activate: add CLAY_API_KEY to .env, POST to Clay enrichment endpoint.
    """
    return {"stub": True, "message": "Clay API integration pending", "inputs": {"company": company_name, "title": title}}
```

### LinkedIn Sales Navigator Stub (`integrations/linkedin_stub.py`)
```python
def find_decision_maker_linkedin(company_name: str, title: str) -> dict:
    """
    STUB: In production, calls LinkedIn Sales Navigator API to find, verify,
    and pull profile data for decision-makers.

    Complements Phase B: confirms job title is current, surfaces mutual
    connections, provides connection degree for outreach personalisation.

    To activate: LinkedIn Sales Navigator enterprise API access + OAuth 2.0 flow.
    """
    return {"stub": True, "message": "LinkedIn Sales Navigator integration pending", "inputs": {"company": company_name, "title": title}}
```

---

## Supabase Migration (required for Vercel deployment)

The current `app/api/leads/route.ts` uses `fs.readFile` / `fs.writeFile`. **This does not work on Vercel** — serverless functions have no persistent filesystem. Supabase is required.

### Steps
1. Create Supabase project, run schema SQL above
2. Add env vars: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
3. Add `supabase>=2.0.0` to `requirements.txt`; update Python pipeline to upsert to Supabase
4. Add `@supabase/supabase-js` to Next.js; create `lib/supabase.ts`
5. Replace GET route: `fs.readFile` → `supabase.from('leads').select('*')`
6. Replace PATCH route: `fs.writeFile` → `supabase.from('leads').update().eq('id', id)`
7. Replace name-slug composite `id` with Supabase UUID throughout frontend
8. Remove `fs` imports from API routes

### Pipeline write (end of `main.py`)
```python
from supabase import create_client
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
supabase.table("leads").upsert(lead_rows, on_conflict="company_name,dm_name").execute()
```

---

## Next.js Dashboard (`dashboard-nextjs/`) — Current State

### Already built ✅
- Next.js 14 App Router, TypeScript, Tailwind CSS, shadcn/ui
- Summary metrics cards (total leads, high fit, open, in progress)
- Filterable lead table (13 columns, sortable, inline editable)
- Sliding detail panel (HubSpot-style, 500px, right side, smooth animation)
- Qualification score breakdown with progress bars
- Copy-to-clipboard for outreach and contact info
- CRM fields editable in panel (status, owner, notes, dates)
- Optimistic UI updates with background sync
- Supabase UUID as lead `id` (already updated in `page.tsx`)

### Still needed ❌
- Replace `fs.readFile` / `fs.writeFile` in API routes with Supabase client calls
- Add `lib/supabase.ts`
- Update `lib/types.ts` for new schema (including `contact_found`, `additional_decision_makers`, `dm_contact_fallback`, `industry_engagement`, `engagement_confidence`)
- Add `@supabase/supabase-js` to `package.json`
- Add Supabase env vars to Vercel project settings

---

## Repo Structure

```
instalily-lead-gen/
├── agents/
│   ├── research_agent.py       # REWRITE: Exa findSimilar + keyword → Claude extraction
│   ├── enrichment_agent.py     # EXPAND: 4 phases (enrich, contacts, events, score)
│   └── outreach_agent.py       # UNCHANGED
├── integrations/
│   ├── exa_client.py
│   ├── clay_stub.py
│   └── linkedin_stub.py
├── data/
│   └── leads.json              # Local backup only — Supabase is source of truth
├── dashboard-nextjs/
│   ├── app/api/leads/route.ts  # Update to Supabase
│   ├── lib/supabase.ts         # New file
│   ├── lib/types.ts            # Update for new schema
│   └── ...
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Environment Variables (`.env.example`)

```
ANTHROPIC_API_KEY=your_key_here
EXA_API_KEY=your_key_here

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Future integrations (stubs only):
# CLAY_API_KEY=your_key_here
# LINKEDIN_API_KEY=your_key_here
```

---

## Error Handling Requirements

- Wrap all API calls in `try/except` (Python) and `try/catch` (TypeScript)
- Pipeline must not crash if one company fails — log error, continue
- If enrichment fails (Phase A): set `enrichment_status: 'failed'`, skip Phases B/C/D
- If contact discovery fails (Phase B): use fallback chain; never discard a company
- Phase C always produces output — fall through confirmed → historical → inferred; `industry_engagement` is never null
- If qualification fails (Phase D): set `label: 'Unknown'`, include raw rationale
- If Supabase write fails: log with company name, continue pipeline
- Dashboard: null/missing fields → "Not available", never crash

---

## Scalability Narrative (describe, do not build)

1. **Parallelise enrichment** — `asyncio` for concurrent Phase A/B/C/D per company
2. **Activate Clay + LinkedIn stubs** — fills the contact discovery gap, verifies emails
3. **Parameterise the ICP** — replace hardcoded Tedlar config with JSON input schema
4. **Schedule pipeline** — GitHub Actions cron → weekly automated refresh → Supabase
5. **Server-side filtering** — move filter logic into Supabase queries
6. **Multi-tenant** — `client_id` column in Supabase, reps see only their client's leads
7. **Evals + RLHF** — score qualification accuracy against rep feedback, improve over time

---

## Build Priority Order

1. ✅ Three Python agents (original structure)
2. ✅ Next.js dashboard (table, panel, filters, CRM editing, API routes)
3. ✅ Supabase UUID as lead ID in frontend
4. **NOW — Research Agent rewrite** (Exa findSimilar + Claude extraction)
5. **NOW — Enrichment Agent expansion** (add Phase B contact discovery, Phase C event enrichment)
6. **NOW — Supabase integration** (replace fs calls in API routes)
7. Deploy to Vercel from GitHub
8. README + documentation PDF (3 pages max)
9. Presentation slides

---

## Key Decisions Log

| Decision | Resolution |
|----------|------------|
| Frontend framework | Next.js 14 App Router (built) |
| Data storage | Supabase Postgres (replaces leads.json) |
| Deployment | Vercel (requires Supabase — fs.writeFile fails on serverless) |
| Agent count | 3 agents; Agent 2 has 4 internal phases |
| Primary discovery mechanism | ICP similarity search (Exa findSimilar + keyword) — NOT event attendee lists |
| Events/conferences | Contextual enrichment in Agent 2 Phase C — not primary source |
| Company extraction | Claude parses Exa results — NOT URL domain extraction |
| Contact discovery | Phase B in Agent 2; fallback chain; companies kept even with no contact |
| Multiple contacts per company | Allowed; stored in `additional_decision_makers` JSONB |
| Qualification scoring | 4-criterion rubric, weighted total out of 100 → High/Medium/Low |
| Dashboard layout | Metrics → filterable table → sliding detail panel (HubSpot-style) |
| Lead ID | Supabase UUID (replaces fragile name-slug composite key) |
| Competitor flagging | competitor_flag: true on Avery Dennison / 3M; included with note |
| Industry engagement model | 3-tier: confirmed (2026 evidence) → historical (2024/2025 attendance) → inferred (ICP profile); always populated, never null; displayed as "Industry Engagement" in dashboard |
| Cron job (future) | GitHub Actions — stateless batch job writing to Supabase; no persistent server needed |
