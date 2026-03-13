# Quick Setup Guide

## Step 1: Install Dependencies

```bash
cd dashboard-nextjs
npm install
```

## Step 2: Verify Data File Location

The dashboard expects the `leads.json` file at:
```
/Users/linus/Desktop/Claude/GTM_agents/data/leads.json
```

If your file is elsewhere, update the path in `app/api/leads/route.ts`:

```typescript
const LEADS_FILE_PATH = path.join(process.cwd(), "..", "data", "leads.json")
```

## Step 3: Run Development Server

```bash
npm run dev
```

Visit: http://localhost:3000

## Step 4: Verify Everything Works

1. You should see metrics cards at the top
2. Lead table should populate with your leads
3. Click a lead name to open the detail panel
4. Try editing the "Lead Status" or "Lead Owner" fields inline
5. Click "Save" in the detail panel to persist changes

## Common Issues

### "Failed to read leads data"
- Check that `data/leads.json` exists
- Verify the file path in `app/api/leads/route.ts`
- Ensure the JSON is valid (run Python pipeline first)

### "No leads match your filters"
- Click "All" on all filter dropdowns
- Check that `data/leads.json` has leads with `crm_data` fields

### TypeScript Errors
- Run `npm install` again
- Delete `node_modules` and `.next`, then reinstall
- Run `npm run type-check` to see specific errors

## Production Build

```bash
npm run build
npm run start
```

This creates an optimized production build.

## Next Steps

1. Run the Python pipeline (`python main.py`) to generate fresh leads
2. Refresh the dashboard to see new data
3. Start managing leads through the UI
4. Export filtered leads to CSV (coming soon)
5. Activate Clay/LinkedIn integrations when ready
