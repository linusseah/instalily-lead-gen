-- Instalily Lead Generation - Supabase Schema
-- Run this in your Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Pipeline Runs Table (metadata for each pipeline execution)
CREATE TABLE pipeline_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  pipeline_version TEXT NOT NULL,
  total_leads INTEGER DEFAULT 0,
  high_fit_count INTEGER DEFAULT 0,
  medium_fit_count INTEGER DEFAULT 0,
  low_fit_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Leads Table (main table with all lead data)
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pipeline_run_id UUID REFERENCES pipeline_runs(id) ON DELETE CASCADE,

  -- Searchable/filterable fields (denormalized for query performance)
  company_name TEXT NOT NULL,
  decision_maker_name TEXT,
  decision_maker_title TEXT,
  decision_maker_linkedin TEXT,
  decision_maker_email TEXT,
  decision_maker_phone TEXT,

  event_name TEXT,
  event_date TEXT,
  event_location TEXT,

  qualification_score INTEGER,
  qualification_label TEXT CHECK (qualification_label IN ('High', 'Medium', 'Low', 'Unknown')),

  -- CRM fields
  lead_status TEXT DEFAULT 'Open' CHECK (lead_status IN ('Open', 'In Progress', 'Unqualified', 'Closed')),
  lead_owner TEXT,
  last_interaction_date DATE,
  notes TEXT,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Full nested data as JSONB for complex structures
  company_data JSONB NOT NULL,
  qualification_data JSONB,
  outreach_data JSONB,
  event_data JSONB,
  decision_maker_data JSONB,

  -- Indexes for common queries
  CONSTRAINT leads_company_name_idx UNIQUE (pipeline_run_id, company_name, decision_maker_name)
);

-- Create indexes for performance
CREATE INDEX idx_leads_company_name ON leads(company_name);
CREATE INDEX idx_leads_qualification_label ON leads(qualification_label);
CREATE INDEX idx_leads_lead_status ON leads(lead_status);
CREATE INDEX idx_leads_event_name ON leads(event_name);
CREATE INDEX idx_leads_pipeline_run ON leads(pipeline_run_id);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);

-- Full-text search index for company descriptions
CREATE INDEX idx_leads_company_data_gin ON leads USING GIN (company_data);

-- Lead Updates Audit Log (track CRM field changes)
CREATE TABLE lead_updates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lead_updates_lead_id ON lead_updates(lead_id);
CREATE INDEX idx_lead_updates_updated_at ON lead_updates(updated_at DESC);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on leads table
CREATE TRIGGER update_leads_updated_at
BEFORE UPDATE ON leads
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - Disabled for single-user setup
-- Can be enabled later for multi-user access
ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_updates ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (single-user setup)
CREATE POLICY "Allow all for authenticated users" ON pipeline_runs
  FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all for authenticated users" ON leads
  FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all for authenticated users" ON lead_updates
  FOR ALL USING (auth.role() = 'authenticated');

-- Allow public read access for anon key (dashboard access)
CREATE POLICY "Allow public read" ON pipeline_runs
  FOR SELECT USING (true);

CREATE POLICY "Allow public read" ON leads
  FOR SELECT USING (true);

-- Allow public updates for CRM fields (dashboard editing)
CREATE POLICY "Allow public updates" ON leads
  FOR UPDATE USING (true);

-- Insert sample pipeline run for testing (optional)
-- INSERT INTO pipeline_runs (pipeline_version, total_leads)
-- VALUES ('1.0.0', 0);
