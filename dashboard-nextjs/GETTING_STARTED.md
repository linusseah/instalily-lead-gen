# Getting Started with Instalily Lead Dashboard

**Welcome!** This guide will get you up and running with the React/Next.js lead management dashboard in under 5 minutes.

## Quick Start (3 Steps)

### 1. Install Dependencies

```bash
cd /Users/linus/Desktop/Claude/GTM_agents/dashboard-nextjs
npm install
```

Expected output:
```
added 342 packages in 45s
```

### 2. Verify Data File

Check that your leads data exists:

```bash
ls -lh ../data/leads.json
```

Should show something like:
```
-rw-r--r--  1 linus  staff   8.2K Mar 11 22:14 ../data/leads.json
```

If the file doesn't exist, generate it:
```bash
cd ..
python main.py
```

### 3. Start the Dashboard

```bash
npm run dev
```

You should see:
```
  ▲ Next.js 14.2.0
  - Local:        http://localhost:3000
  - Ready in 1.2s
```

**Open your browser to: http://localhost:3000**

---

## What You Should See

### 1. Header
```
Instalily Lead Dashboard
DuPont Tedlar • AI-Powered Lead Intelligence
```

### 2. Metrics Cards (4 across)
- **Total Leads**: Total count from your data
- **High Fit Leads**: Count of leads with fit score ≥70
- **Open Leads**: Leads with status = "Open"
- **In Progress**: Leads with status = "In Progress"

### 3. Filters Section
Three dropdowns:
- **Lead Owner**: Filter by sales rep
- **Lead Status**: Filter by Open/In Progress/Unqualified/Closed
- **Fit Score**: Filter by High/Medium/Low

Plus a "Score Info" button that explains the scoring methodology.

### 4. Lead Table
13 columns showing all lead information:
1. Name (clickable)
2. Title
3. Lead Status (editable)
4. Company
5. Website (linked)
6. Industry (auto-classified)
7. Lead Owner (editable)
8. Email
9. Phone
10. LinkedIn (linked)
11. Last Interaction
12. Created Date
13. Fit Score (color-coded)

---

## First Actions to Try

### ✅ Filter Leads
1. Click the "Fit Score" dropdown
2. Select "High"
3. Table instantly filters to show only high-fit leads

### ✅ Sort Leads
1. Click the "Fit Score" column header
2. Leads sort by score (highest first)
3. Click again to reverse order

### ✅ View Lead Details
1. Click any lead's **Name** in the table
2. A panel slides in from the right
3. Shows complete lead information, outreach message, and score breakdown

### ✅ Edit Lead Status (Inline)
1. Click the status **badge** in the table
2. A dropdown appears
3. Select new status (e.g., "In Progress")
4. Changes save automatically

### ✅ Edit Lead Owner (Inline)
1. Click the **Lead Owner** cell (shows "—" if empty)
2. A text input appears
3. Type a name (e.g., "John Doe")
4. Press Enter or click away
5. Changes save automatically

### ✅ Copy Outreach Message
1. Open a lead detail panel (click name)
2. Scroll to "Recommended Outreach" section
3. Click "Copy Outreach" button
4. Message is copied to clipboard
5. Button shows checkmark for 2 seconds

---

## Understanding the Data

### Where Does Data Come From?

```
Python Pipeline (main.py)
    ↓
Agents (research, enrichment, outreach)
    ↓
data/leads.json (saved here)
    ↓
Next.js Dashboard (reads from here)
```

### Data Update Workflow

1. Run Python pipeline to generate new leads:
   ```bash
   cd /Users/linus/Desktop/Claude/GTM_agents
   python main.py
   ```

2. Refresh dashboard to see new leads:
   - Click "Refresh" button in header, OR
   - Reload browser page (Cmd+R / Ctrl+R)

### How Updates Work

When you edit a lead in the dashboard:

1. **Inline edit** → Auto-saves to `leads.json` on blur/Enter
2. **Detail panel** → Click "Save Changes" to persist

The dashboard writes changes back to the **same** `leads.json` file that the Python pipeline reads.

---

## Understanding Fit Scores

### Score Calculation

Each lead gets scored on 4 criteria (0-10 each):

| Criterion | Weight | What It Measures |
|-----------|--------|------------------|
| **Industry Fit** | 30% | Alignment with large-format signage, vehicle wraps, architectural graphics |
| **Size & Revenue** | 20% | Company scale (>$50M revenue or 200+ employees preferred) |
| **Strategic Relevance** | 30% | Use/specify protective overlaminates or durable graphic films |
| **Event Engagement** | 20% | Active in ISA, PRINTING United, FESPA, SEGD events |

**Weighted Total** = Sum of (score × weight)

**Label Mapping**:
- **High** (green): ≥70 points
- **Medium** (yellow): 40-69 points
- **Low** (red): <40 points

### Example: swissQprint

```
Industry Fit:        9/10 (30%) = 27 points
Size & Revenue:      6/10 (20%) = 12 points
Strategic Relevance: 7/10 (30%) = 21 points
Event Engagement:    8/10 (20%) = 16 points
                                  ─────────
Weighted Total:                   76 points → HIGH
```

---

## Common Tasks

### Find All High-Fit Leads Without an Owner

1. Set **Fit Score** filter to "High"
2. Set **Lead Owner** filter to "All"
3. Scan table for rows where Lead Owner shows "—"
4. Assign yourself by clicking the cell and typing your name

### Export Leads to CSV (Manual)

*Note: CSV export feature is planned but not yet implemented.*

For now, you can:
1. Open `data/leads.json` in a text editor
2. Use a JSON-to-CSV converter tool
3. Or copy relevant data from the table

### Review All Leads from a Specific Event

Unfortunately, event filtering is not currently in the filters.

**Workaround**:
1. Open detail panel for each lead
2. Check "Event Source" section
3. Filter manually based on event name

*This would be a good feature to add!*

### Mark Leads as Contacted

1. Click lead name to open detail panel
2. Scroll to "CRM Data" section
3. Change **Lead Status** to "In Progress"
4. Set **Last Interaction Date** to today
5. Add notes (e.g., "Sent initial email")
6. Click "Save Changes"

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Tab** | Navigate between editable fields |
| **Enter** | Save inline edit (Lead Owner field) |
| **Escape** | Close detail panel (when panel is focused) |
| **Click overlay** | Close detail panel |

---

## Troubleshooting

### Issue: Dashboard shows "Loading leads..." forever

**Cause**: API can't read `leads.json` file

**Solution**:
1. Check that file exists: `ls ../data/leads.json`
2. If missing, run: `cd .. && python main.py`
3. Refresh browser

### Issue: "No leads match your filters"

**Cause**: Filters are too restrictive

**Solution**:
1. Set all filters to "All"
2. Leads should appear
3. Adjust filters one at a time

### Issue: Inline edits aren't saving

**Cause**: API route error

**Solution**:
1. Check browser console (F12 → Console tab)
2. Look for red error messages
3. Check terminal where `npm run dev` is running
4. Copy error message and check SETUP.md

### Issue: Detail panel won't open

**Cause**: JavaScript error

**Solution**:
1. Open browser console (F12)
2. Look for error messages
3. Refresh page (Cmd+R / Ctrl+R)
4. Try clicking a different lead

### Issue: Metrics show 0 for everything

**Cause**: Data file is empty or malformed

**Solution**:
1. Check `data/leads.json` has leads
2. Run Python pipeline: `python main.py`
3. Refresh dashboard

---

## File Locations

| File | Purpose | Path |
|------|---------|------|
| **Lead data** | Source of truth | `/Users/linus/Desktop/Claude/GTM_agents/data/leads.json` |
| **Dashboard code** | React/Next.js app | `/Users/linus/Desktop/Claude/GTM_agents/dashboard-nextjs/` |
| **API routes** | Read/write leads | `dashboard-nextjs/app/api/leads/route.ts` |
| **Main page** | Dashboard UI | `dashboard-nextjs/app/page.tsx` |
| **Types** | TypeScript definitions | `dashboard-nextjs/lib/types.ts` |

---

## Next Steps

### Learn More
- Read **README.md** for comprehensive documentation
- Read **ARCHITECTURE.md** for technical details
- Read **MIGRATION_GUIDE.md** if migrating from Streamlit

### Customize
- Add new filters (see README.md)
- Add new table columns (see README.md)
- Change color schemes (edit `tailwind.config.ts`)

### Deploy to Production
- Push code to GitHub
- Deploy on Vercel (free tier)
- Share URL with team

---

## Getting Help

### Documentation Files (In Order of Usefulness)
1. **GETTING_STARTED.md** ← You are here
2. **SETUP.md** - Quick installation guide
3. **README.md** - Full documentation
4. **MIGRATION_GUIDE.md** - Streamlit → Next.js
5. **ARCHITECTURE.md** - Technical deep dive
6. **PROJECT_SUMMARY.md** - What was built

### Check for Errors
- **Browser Console**: F12 → Console tab
- **Server Logs**: Terminal where `npm run dev` is running
- **TypeScript Errors**: Run `npm run type-check`

### Common Questions

**Q: Can I run this alongside Streamlit?**
A: Yes! Both read from the same `leads.json` file.

**Q: Will edits in Next.js show in Streamlit?**
A: Yes, after you refresh Streamlit (it re-reads the file).

**Q: Can I change the data file location?**
A: Yes, edit `LEADS_FILE_PATH` in `app/api/leads/route.ts`

**Q: How do I add more CRM fields?**
A: Update `CRMData` interface in `lib/types.ts`, then update the form in `LeadDetailPanel.tsx`

**Q: How do I deploy to production?**
A: See README.md → Deployment section

---

## Success!

If you can see leads in the table and open the detail panel, you're all set!

**What to do next:**
1. Explore the dashboard features
2. Try filtering and editing leads
3. Review the recommended outreach messages
4. Assign leads to team members
5. Start working your pipeline!

**Happy selling!** 🚀
