# Supabase Setup Guide

This guide will help you set up Supabase as the database backend for the Instalily Lead Generation pipeline.

## Prerequisites

- A Supabase account (free tier works fine)
- Node.js and Python installed locally

---

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Fill in:
   - **Project Name**: `instalily-leads` (or any name)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to you
4. Click "Create new project"
5. Wait 2-3 minutes for project to initialize

---

## Step 2: Run Database Schema

1. In your Supabase project, go to the **SQL Editor** (left sidebar)
2. Click "New Query"
3. Copy the entire contents of `supabase/schema.sql` from this repo
4. Paste into the SQL Editor
5. Click **Run** (or press Cmd/Ctrl + Enter)
6. You should see: `Success. No rows returned`

This creates 3 tables:
- `pipeline_runs` - Metadata for each pipeline execution
- `leads` - Main lead data
- `lead_updates` - Audit log for CRM changes

---

## Step 3: Get API Credentials

1. Go to **Project Settings** (gear icon in left sidebar)
2. Click **API** in the left menu
3. Copy these two values:
   - **Project URL** (looks like `https://xxxxx.supabase.co`)
   - **anon public** key (long string under "Project API keys")

---

## Step 4: Configure Python Environment

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Supabase credentials:
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here
   ```

3. Install the Supabase Python client:
   ```bash
   pip install -r requirements.txt
   ```

---

## Step 5: Configure Next.js Dashboard

1. Navigate to the dashboard directory:
   ```bash
   cd dashboard-nextjs
   ```

2. Copy `.env.local.example` to `.env.local`:
   ```bash
   cp .env.local.example .env.local
   ```

3. Edit `.env.local` and add the SAME Supabase credentials:
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
   ```

4. Install Node dependencies:
   ```bash
   npm install
   ```

---

## Step 6: Test the Connection

### Test Python Connection

```bash
# Run from the repo root
python -c "from integrations.supabase_client import SupabaseClient; client = SupabaseClient(); print('✓ Python Supabase connection successful!')"
```

You should see: `✓ Python Supabase connection successful!`

### Test Next.js Connection

```bash
cd dashboard-nextjs
npm run dev
```

Then visit `http://localhost:3000` - dashboard should load (even if empty)

---

## Step 7: Run the Pipeline

1. Run a test pipeline to generate leads:
   ```bash
   python main.py --test
   ```

2. You should see:
   ```
   Writing to Supabase database...
   ✓ Created pipeline run: <UUID>
   ✓ Inserted X new leads to Supabase
   ✓ Updated pipeline statistics
   ```

3. Verify in Supabase:
   - Go to **Table Editor** in Supabase dashboard
   - Click on `leads` table
   - You should see your test leads!

---

## Step 8: View in Dashboard

1. Start the Next.js dashboard:
   ```bash
   cd dashboard-nextjs
   npm run dev
   ```

2. Open `http://localhost:3000`
3. You should see your leads from Supabase!
4. Test editing a lead (change status, add notes) - changes save to Supabase

---

## Troubleshooting

### "Missing Supabase credentials" Error

- Double-check `.env` and `.env.local` files have correct values
- Make sure you copied the **anon public** key, not the **service_role** key
- Restart the dev server after changing env files

### "Relation 'leads' does not exist"

- You didn't run the schema SQL file
- Go back to Step 2 and run `supabase/schema.sql` in the SQL Editor

### Dashboard shows "Error reading leads"

- Check browser console (F12) for errors
- Verify `NEXT_PUBLIC_` prefix in `.env.local` (required for Next.js)
- Restart `npm run dev` after env changes

### Python pipeline fails with Supabase error

- Check `.env` file has correct credentials
- Test connection from repo root: `python -c "from integrations.supabase_client import SupabaseClient; SupabaseClient()"`

---

## Data Flow Summary

```
Python Pipeline (main.py)
    ↓
Writes to Supabase Database
    ↓
Next.js API (/api/leads)
    ↓
Reads from Supabase
    ↓
Dashboard UI displays leads
```

**Backup:** Pipeline also writes to `data/leads.json` as a local backup.

---

## Next Steps

- Deploy Next.js dashboard to Vercel (see VERCEL_DEPLOY.md)
- Set up scheduled pipeline runs (GitHub Actions cron)
- Add more advanced Supabase features (real-time, analytics)

---

## Security Notes

- The `anon public` key is safe to expose in frontend code
- Row Level Security (RLS) is enabled but permissive for single-user setup
- For multi-user access, update RLS policies in `schema.sql`
- Never commit `.env` or `.env.local` files to git (already in `.gitignore`)
