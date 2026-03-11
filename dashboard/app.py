"""
Instalily Lead Intelligence Dashboard
Streamlit app for viewing and managing enriched leads.
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Instalily - Lead Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# File path
LEADS_FILE = Path("data/leads.json")


def load_leads():
    """Load leads from JSON file."""
    if not LEADS_FILE.exists():
        return None

    with open(LEADS_FILE, 'r') as f:
        data = json.load(f)

    return data


def save_leads(data):
    """Save leads back to JSON file."""
    with open(LEADS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_fit_badge(label):
    """Return colored badge for fit score label."""
    if label == "High":
        return "🟢 High"
    elif label == "Medium":
        return "🟡 Medium"
    elif label == "Low":
        return "🔴 Low"
    else:
        return "⚪ Unknown"


def main():
    # Header
    st.title("📊 Instalily — DuPont Tedlar Lead Intelligence Dashboard")

    # Load data
    data = load_leads()

    if data is None:
        st.warning("No lead data found. Run the pipeline first: `python main.py`")
        st.info("Expected file location: `data/leads.json`")
        return

    leads = data.get('leads', [])

    if not leads:
        st.warning("No leads found in data file.")
        return

    # Subheader with metadata
    generated_at = data.get('generated_at', 'Unknown')
    try:
        dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        formatted_time = generated_at

    st.caption(f"Pipeline run: {formatted_time} | Total leads: {len(leads)}")

    # Section 1: Summary Metrics
    st.markdown("---")

    high_fit = sum(1 for lead in leads if lead.get('qualification', {}).get('label') == 'High')
    medium_fit = sum(1 for lead in leads if lead.get('qualification', {}).get('label') == 'Medium')
    low_fit = sum(1 for lead in leads if lead.get('qualification', {}).get('label') == 'Low')
    outreach_drafted = sum(1 for lead in leads if lead.get('outreach', {}) and lead['outreach'].get('status') == 'draft')

    events = set()
    for lead in leads:
        event_name = lead.get('event', {}).get('name')
        if event_name:
            events.add(event_name)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Leads", len(leads))
    with col2:
        st.metric("High Fit Leads", high_fit)
    with col3:
        st.metric("Outreach Drafted", outreach_drafted)
    with col4:
        st.metric("Events Covered", len(events))

    st.markdown("---")

    # Section 2: Sidebar Filters
    st.sidebar.header("Filters")

    # Event filter
    event_options = ["All Events"] + sorted(list(events))
    selected_event = st.sidebar.selectbox("Filter by Event", event_options)

    # Fit score filter
    fit_options = ["All", "High", "Medium", "Low", "Unknown"]
    selected_fit = st.sidebar.multiselect("Filter by Fit Score", fit_options, default=["All"])

    # Show integration stubs toggle
    show_stubs = st.sidebar.checkbox("Show Integration Stubs", value=False)

    # Download button
    st.sidebar.markdown("---")
    if st.sidebar.button("Download Filtered Leads as CSV"):
        # Convert to DataFrame and download
        df_data = []
        for lead in leads:
            df_data.append({
                "Event": lead.get('event', {}).get('name', ''),
                "Company": lead['company']['name'],
                "Revenue": lead['company'].get('revenue_estimate', ''),
                "Size": lead['company'].get('size', ''),
                "Fit Score": lead.get('qualification', {}).get('weighted_total', 0),
                "Fit Label": lead.get('qualification', {}).get('label', ''),
                "Decision Maker": lead.get('decision_maker', {}).get('name', '') if lead.get('decision_maker') else '',
                "Title": lead.get('decision_maker', {}).get('title', '') if lead.get('decision_maker') else '',
                "LinkedIn": lead.get('decision_maker', {}).get('linkedin', '') if lead.get('decision_maker') else '',
                "Outreach Status": lead.get('outreach', {}).get('status', '') if lead.get('outreach') else ''
            })

        df = pd.DataFrame(df_data)
        csv = df.to_csv(index=False)
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"instalily_leads_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # Apply filters
    filtered_leads = leads

    if selected_event != "All Events":
        filtered_leads = [l for l in filtered_leads if l.get('event', {}).get('name') == selected_event]

    if "All" not in selected_fit:
        filtered_leads = [l for l in filtered_leads if l.get('qualification', {}).get('label') in selected_fit]

    # Section 3: Lead Table
    st.subheader(f"Leads ({len(filtered_leads)})")

    if not filtered_leads:
        st.info("No leads match the current filters.")
        return

    # Display leads
    for i, lead in enumerate(filtered_leads):
        company_name = lead['company']['name']
        event_name = lead.get('event', {}).get('name', 'Unknown Event')
        revenue = lead['company'].get('revenue_estimate', 'Unknown')
        fit_label = lead.get('qualification', {}).get('label', 'Unknown')
        fit_badge = get_fit_badge(fit_label)
        dm = lead.get('decision_maker')
        dm_name = dm.get('name') if dm else "No decision-maker"
        dm_title = dm.get('title') if dm else ""
        linkedin_url = dm.get('linkedin') if dm else None
        outreach_status = lead.get('outreach', {}).get('status', 'N/A') if lead.get('outreach') else 'N/A'
        competitor_flag = lead['company'].get('competitor_flag', False)

        # Lead row
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 2, 1])

            with col1:
                if competitor_flag:
                    st.markdown(f"**{company_name}** ⚠️")
                    st.caption("Competitor")
                else:
                    st.markdown(f"**{company_name}**")
                st.caption(event_name)

            with col2:
                st.write(f"Revenue: {revenue}")

            with col3:
                st.write(fit_badge)

            with col4:
                st.write(f"{dm_name}")
                if dm_title:
                    st.caption(dm_title)
                if linkedin_url:
                    st.markdown(f"[LinkedIn]({linkedin_url})")

            with col5:
                # Expand button
                expand_key = f"expand_{i}"
                if st.button("Expand", key=expand_key):
                    st.session_state[f"expanded_{i}"] = not st.session_state.get(f"expanded_{i}", False)

        # Expanded card
        if st.session_state.get(f"expanded_{i}", False):
            with st.expander("Lead Details", expanded=True):
                # Event info
                st.markdown("### Event")
                st.write(f"**{event_name}**")
                st.write(f"📅 {lead.get('event', {}).get('date', 'N/A')} | 📍 {lead.get('event', {}).get('location', 'N/A')}")
                st.caption(lead.get('event', {}).get('relevance', ''))

                # Company info
                st.markdown("### Company")
                st.write(lead['company'].get('description', 'No description available'))
                st.write(f"🌐 {lead['company'].get('website', 'N/A')}")
                if competitor_flag:
                    st.warning("⚠️ Competitor Flag: This company is a known competitor in some product lines.")

                # Qualification breakdown
                st.markdown("### Qualification Breakdown")
                qualification = lead.get('qualification', {})
                scores = qualification.get('scores', {})

                if scores:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Industry Fit", f"{scores.get('industry_fit', 0)}/10")
                        st.metric("Strategic Relevance", f"{scores.get('strategic_relevance', 0)}/10")
                    with col2:
                        st.metric("Size & Revenue", f"{scores.get('size_and_revenue', 0)}/10")
                        st.metric("Event Engagement", f"{scores.get('event_engagement', 0)}/10")

                    st.metric("**Weighted Total**", f"{qualification.get('weighted_total', 0)}/100")
                    st.write(f"**Label:** {get_fit_badge(qualification.get('label', 'Unknown'))}")

                st.write(f"**Rationale:** {qualification.get('rationale', 'N/A')}")

                # Decision-maker
                if dm and dm.get('name'):
                    st.markdown("### Decision-Maker")
                    st.write(f"**{dm['name']}** — {dm.get('title', 'N/A')}")
                    if linkedin_url:
                        st.markdown(f"[LinkedIn Profile]({linkedin_url})")

                    # Show stubs if enabled
                    if show_stubs:
                        st.info(f"🔌 {dm.get('clay_stub', 'Clay API stub not configured')}")
                        st.info(f"🔌 {dm.get('linkedin_stub', 'LinkedIn API stub not configured')}")

                # Outreach message
                outreach = lead.get('outreach')
                if outreach and outreach.get('message'):
                    st.markdown("### Outreach Message")
                    st.write(f"**Subject:** {outreach.get('subject', 'N/A')}")
                    st.text_area("Message", outreach['message'], height=200, key=f"outreach_{i}")

                    # Copy to clipboard button
                    if st.button("Copy to Clipboard", key=f"copy_{i}"):
                        st.success("Message copied! (Note: Clipboard functionality requires additional Streamlit component)")

                    # Status toggle
                    st.write(f"**Status:** {outreach.get('status', 'N/A')}")
                    new_status = st.selectbox(
                        "Update Status",
                        ["draft", "reviewed", "sent"],
                        index=["draft", "reviewed", "sent"].index(outreach.get('status', 'draft')),
                        key=f"status_{i}"
                    )

                    if st.button("Save Status", key=f"save_status_{i}"):
                        # Update status in data
                        data['leads'][filtered_leads.index(lead)]['outreach']['status'] = new_status
                        save_leads(data)
                        st.success(f"Status updated to: {new_status}")
                        st.rerun()

        st.markdown("---")


if __name__ == "__main__":
    main()
