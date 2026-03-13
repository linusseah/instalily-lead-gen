"""
Instalily Lead Intelligence Dashboard
CRM-style Streamlit app for viewing and managing enriched leads.
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, date
import pyperclip  # For clipboard functionality

# Page config
st.set_page_config(
    page_title="Instalily - Lead Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# File path
LEADS_FILE = Path("data/leads.json")


def load_leads():
    """Load leads from JSON file."""
    if not LEADS_FILE.exists():
        return None

    with open(LEADS_FILE, 'r') as f:
        data = json.load(f)

    # Ensure each lead has editable fields
    for lead in data.get('leads', []):
        if 'crm_data' not in lead:
            lead['crm_data'] = {
                'lead_status': 'Open',
                'lead_owner': '',
                'last_interaction_date': None,
                'created_date': data.get('generated_at', datetime.now().isoformat()),
                'notes': ''
            }

    return data


def save_leads(data):
    """Save leads back to JSON file."""
    with open(LEADS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_industry_from_lead(lead):
    """Extract industry from lead data."""
    description = lead.get('company', {}).get('description', '').lower()

    # Simple keyword matching for industry classification
    if 'vehicle wrap' in description or 'fleet graphic' in description:
        return 'Vehicle Wraps & Fleet Graphics'
    elif 'sign' in description and 'architectural' in description:
        return 'Architectural Signage'
    elif 'large format' in description or 'wide format' in description:
        return 'Large Format Printing'
    elif 'protective film' in description or 'overlaminate' in description:
        return 'Protective Films'
    else:
        return 'Graphics & Signage'


def main():
    # Custom CSS for better styling
    st.markdown("""
        <style>
        /* Make table more compact and readable */
        .stDataFrame {
            font-size: 14px;
        }

        /* Make data editor more compact */
        [data-testid="stDataFrameResizable"] {
            font-size: 13px;
        }

        /* Compact metrics */
        [data-testid="stMetricValue"] {
            font-size: 24px;
        }

        /* Timestamp styling */
        .timestamp-label {
            background-color: #f0f2f6;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            color: #31333F;
            margin-bottom: 10px;
            display: inline-block;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.title("📊 Instalily — Lead Intelligence Dashboard")

    # Load data
    data = load_leads()

    if data is None:
        st.warning("No lead data found. Run the pipeline first: `python main.py --test`")
        st.info("Expected file location: `data/leads.json`")
        return

    leads = data.get('leads', [])

    if not leads:
        st.warning("No leads found in data file.")
        return

    # Extract and format pipeline timestamp
    generated_at = data.get('generated_at', 'Unknown')
    try:
        dt = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        formatted_time = generated_at

    # Summary Metrics
    st.markdown("---")

    high_fit = sum(1 for lead in leads if lead.get('qualification', {}).get('label') == 'High')
    open_leads = sum(1 for lead in leads if lead.get('crm_data', {}).get('lead_status') == 'Open')
    in_progress = sum(1 for lead in leads if lead.get('crm_data', {}).get('lead_status') == 'In Progress')

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Leads", len(leads))
    with col2:
        st.metric("High Fit", high_fit)
    with col3:
        st.metric("Open", open_leads)
    with col4:
        st.metric("In Progress", in_progress)

    st.markdown("---")

    # Filters Section
    st.subheader("🔍 Filters")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        # Lead Owner filter
        all_owners = set()
        for lead in leads:
            owner = lead.get('crm_data', {}).get('lead_owner', '')
            if owner:
                all_owners.add(owner)

        owner_options = ["All"] + sorted(list(all_owners))
        selected_owner = st.selectbox("Lead Owner", owner_options)

    with filter_col2:
        # Lead Status filter
        status_options = ["All", "Open", "In Progress", "Unqualified", "Closed"]
        selected_status = st.selectbox("Lead Status", status_options)

    with filter_col3:
        # Fit filter
        fit_options = ["All", "High", "Medium", "Low"]
        selected_fit = st.selectbox("Fit Score", fit_options)

    with filter_col4:
        # Download CSV
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("📥 Download CSV"):
            # Prepare CSV data
            csv_data = []
            for lead in leads:
                dm = lead.get('decision_maker', {})
                crm = lead.get('crm_data', {})
                csv_data.append({
                    "Name": dm.get('name', ''),
                    "Title": dm.get('title', ''),
                    "Lead Status": crm.get('lead_status', 'Open'),
                    "Company": lead['company']['name'],
                    "Industry": get_industry_from_lead(lead),
                    "Lead Owner": crm.get('lead_owner', ''),
                    "Email": dm.get('email', ''),
                    "Phone": dm.get('phone', ''),
                    "LinkedIn": dm.get('linkedin', ''),
                    "Last Interaction": crm.get('last_interaction_date', ''),
                    "Created Date": crm.get('created_date', ''),
                    "Fit Score": lead.get('qualification', {}).get('weighted_total', 0),
                    "Fit Label": lead.get('qualification', {}).get('label', ''),
                    "Company Website": lead['company'].get('website', ''),
                    "Revenue": lead['company'].get('revenue_estimate', ''),
                    "Size": lead['company'].get('size', '')
                })

            df_csv = pd.DataFrame(csv_data)
            csv = df_csv.to_csv(index=False)
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"instalily_leads_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    # Apply filters
    filtered_leads = leads.copy()

    if selected_owner != "All":
        filtered_leads = [l for l in filtered_leads if l.get('crm_data', {}).get('lead_owner') == selected_owner]

    if selected_status != "All":
        filtered_leads = [l for l in filtered_leads if l.get('crm_data', {}).get('lead_status') == selected_status]

    if selected_fit != "All":
        filtered_leads = [l for l in filtered_leads if l.get('qualification', {}).get('label') == selected_fit]

    st.markdown("---")

    # Main Table Section with timestamp
    st.subheader(f"Leads ({len(filtered_leads)})")

    # Timestamp label
    st.markdown(f'<div class="timestamp-label">📅 Last data pull: {formatted_time}</div>', unsafe_allow_html=True)
    st.write("")  # Spacing

    if not filtered_leads:
        st.info("No leads match the current filters.")
        return

    # Build editable table data
    table_data = []
    for idx, lead in enumerate(filtered_leads):
        dm = lead.get('decision_maker', {})
        crm = lead.get('crm_data', {})
        company = lead.get('company', {})

        # Format created date
        created_date = crm.get('created_date', '')
        try:
            if created_date:
                dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                created_date = dt.strftime('%Y-%m-%d')
        except:
            pass

        # Format last interaction date
        last_interaction = crm.get('last_interaction_date', '')

        table_data.append({
            "_original_idx": idx,  # Track which lead this is
            "Name": dm.get('name', 'No DM'),
            "Title": dm.get('title', ''),
            "Lead Status": crm.get('lead_status', 'Open'),
            "Company": company.get('name', ''),
            "Company URL": company.get('website', ''),
            "Industry": get_industry_from_lead(lead),
            "Lead Owner": crm.get('lead_owner', ''),
            "Email": dm.get('email') if dm.get('email') else 'Clay API',
            "Phone": dm.get('phone') if dm.get('phone') else '',
            "LinkedIn": dm.get('linkedin', ''),
            "Last Interaction": last_interaction,
            "Created Date": created_date,
            "Fit": lead.get('qualification', {}).get('label', 'Unknown')
        })

    df = pd.DataFrame(table_data)

    # Configure editable columns
    column_config = {
        "_original_idx": None,  # Hide
        "Name": st.column_config.TextColumn("Name", width="medium", disabled=True),
        "Title": st.column_config.TextColumn("Title", width="medium", disabled=True),
        "Lead Status": st.column_config.SelectboxColumn(
            "Lead Status",
            width="small",
            options=["Open", "In Progress", "Unqualified", "Closed"],
            required=True
        ),
        "Company": st.column_config.TextColumn("Company", width="medium", disabled=True),
        "Company URL": st.column_config.LinkColumn("Website", width="small", disabled=True),
        "Industry": st.column_config.TextColumn("Industry", width="medium", disabled=True),
        "Lead Owner": st.column_config.TextColumn("Lead Owner", width="small"),
        "Email": st.column_config.TextColumn("Email", width="medium", disabled=True),
        "Phone": st.column_config.TextColumn("Phone", width="small", disabled=True),
        "LinkedIn": st.column_config.LinkColumn("LinkedIn", width="small", disabled=True),
        "Last Interaction": st.column_config.TextColumn("Last Interaction", width="small", disabled=True),
        "Created Date": st.column_config.TextColumn("Created", width="small", disabled=True),
        "Fit": st.column_config.TextColumn("Fit", width="small", disabled=True)
    }

    # Display editable table
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        height=500,
        num_rows="fixed",
        key="lead_table"
    )

    # Check for changes and save
    if not edited_df.equals(df):
        # Update the data with changes
        for idx, row in edited_df.iterrows():
            original_idx = row['_original_idx']
            lead = filtered_leads[original_idx]

            # Find in full leads list
            full_idx = next(
                (i for i, l in enumerate(data['leads'])
                 if l['company']['name'] == lead['company']['name']),
                None
            )

            if full_idx is not None:
                # Update lead status and owner
                data['leads'][full_idx]['crm_data']['lead_status'] = row['Lead Status']
                data['leads'][full_idx]['crm_data']['lead_owner'] = row['Lead Owner']

        save_leads(data)
        st.success("✅ Changes saved!")
        st.rerun()

    # Lead Selection for Detail View
    st.markdown("---")

    # Fit Score Calculation Explanation (Collapsible)
    with st.expander("ℹ️ How Fit Scores Are Calculated", expanded=False):
        st.markdown("""
        ### Fit Score Breakdown

        Each lead is scored on **4 criteria** (0-10 scale), which are weighted and combined into a total score out of 100:

        | Criterion | Weight | What We Evaluate |
        |-----------|--------|------------------|
        | **Industry Fit** | 30% | Is the company's core business in large-format signage, vehicle wraps, fleet graphics, or architectural graphics? |
        | **Size & Revenue** | 20% | Company size and revenue. Preference for >$50M revenue or 200+ employees. |
        | **Strategic Relevance** | 30% | Does the company use, specify, or produce protective overlaminates or durable graphic films that Tedlar could supply? |
        | **Event & Association Engagement** | 20% | Active participation in ISA, PRINTING United, FESPA, or SEGD events? |

        **Scoring Scale:**
        - **9-10**: Excellent fit
        - **6-8**: Good fit
        - **3-5**: Moderate fit
        - **0-2**: Poor fit

        **Final Label:**
        - **High**: 70-100 (strong ICP match)
        - **Medium**: 40-69 (moderate ICP match)
        - **Low**: 0-39 (weak ICP match)

        **Formula:**
        `Total Score = (Industry Fit × 0.30 + Size & Revenue × 0.20 + Strategic Relevance × 0.30 + Event Engagement × 0.20) × 10`
        """)

    col_select1, col_select2 = st.columns([3, 1])

    with col_select1:
        st.write("**Select a lead to view details and edit:**")

    with col_select2:
        selected_row = st.selectbox(
            "Row #",
            options=list(range(1, len(filtered_leads) + 1)),
            key="lead_selector"
        )

    # Detail View
    if selected_row:
        lead_idx = selected_row - 1
        lead = filtered_leads[lead_idx]

        # Find original index in full leads list
        original_idx = next(
            (i for i, l in enumerate(data['leads'])
             if l['company']['name'] == lead['company']['name']),
            None
        )

        st.markdown("---")

        # Two column layout: Left = details, Right = editable fields
        detail_col1, detail_col2 = st.columns([2, 1])

        with detail_col1:
            # Lead Details Panel
            dm = lead.get('decision_maker', {})
            company = lead.get('company', {})
            qualification = lead.get('qualification', {})
            outreach = lead.get('outreach', {})

            st.markdown(f"### 👤 {dm.get('name', 'No Decision Maker')}")
            st.write(f"**{dm.get('title', 'No Title')}**")

            # Contact Info with Copy Buttons
            st.markdown("#### 📧 Contact Information")

            email = dm.get('email')
            if email:
                col_e1, col_e2 = st.columns([4, 1])
                with col_e1:
                    st.text_input("Email", email, key=f"email_display_{lead_idx}", disabled=True)
                with col_e2:
                    st.write("")
                    st.write("")
                    if st.button("📋", key=f"copy_email_{lead_idx}"):
                        try:
                            pyperclip.copy(email)
                            st.success("Copied!")
                        except:
                            st.code(email)
                            st.caption("Manual copy required")
            else:
                st.info("📧 Email: Clay API stub — contact enrichment pending")

            linkedin = dm.get('linkedin')
            if linkedin:
                st.markdown(f"🔗 [LinkedIn Profile]({linkedin})")
            else:
                st.info("🔗 LinkedIn: Sales Navigator API stub — profile lookup pending")

            phone = dm.get('phone')
            if phone:
                st.text_input("Phone", phone, key=f"phone_display_{lead_idx}", disabled=True)

            # Company Info
            st.markdown("#### 🏢 Company Information")
            st.write(f"**{company.get('name', 'Unknown Company')}**")
            st.write(f"🌐 [{company.get('website', 'No website')}]({company.get('website', '#')})")
            st.write(f"💰 Revenue: {company.get('revenue_estimate', 'Unknown')}")
            st.write(f"👥 Size: {company.get('size', 'Unknown')}")

            st.markdown("**Description:**")
            st.write(company.get('description', 'No description available'))

            # Fit Score Breakdown (renamed from Qualification)
            st.markdown("#### 📊 Fit Score Breakdown")
            scores = qualification.get('scores', {})

            if scores:
                q_col1, q_col2 = st.columns(2)
                with q_col1:
                    st.metric("Industry Fit (30%)", f"{scores.get('industry_fit', 0)}/10")
                    st.metric("Strategic Relevance (30%)", f"{scores.get('strategic_relevance', 0)}/10")
                with q_col2:
                    st.metric("Size & Revenue (20%)", f"{scores.get('size_and_revenue', 0)}/10")
                    st.metric("Event Engagement (20%)", f"{scores.get('event_engagement', 0)}/10")

                st.metric("**Total Score**",
                         f"{qualification.get('weighted_total', 0)}/100 — {qualification.get('label', 'Unknown')}")

            st.markdown("**Rationale:**")
            st.write(qualification.get('rationale', 'No rationale available'))

            # Recommended Outreach
            st.markdown("#### ✉️ Recommended Outreach")
            if outreach and outreach.get('message'):
                st.write(f"**Subject:** {outreach.get('subject', 'No subject')}")
                st.text_area(
                    "Message",
                    outreach.get('message', 'No message'),
                    height=200,
                    key=f"outreach_msg_{lead_idx}",
                    disabled=True
                )

                if st.button("📋 Copy Outreach to Clipboard", key=f"copy_outreach_{lead_idx}"):
                    full_message = f"Subject: {outreach.get('subject', '')}\n\n{outreach.get('message', '')}"
                    try:
                        pyperclip.copy(full_message)
                        st.success("✅ Outreach copied to clipboard!")
                    except:
                        st.code(full_message)
                        st.warning("⚠️ Automatic clipboard copy not supported. Please copy manually from above.")
            else:
                st.info("No outreach message available")

        with detail_col2:
            # Editable CRM Fields
            st.markdown("### ✏️ Edit Lead")

            crm = lead.get('crm_data', {})

            # Lead Status
            new_status = st.selectbox(
                "Lead Status",
                ["Open", "In Progress", "Unqualified", "Closed"],
                index=["Open", "In Progress", "Unqualified", "Closed"].index(
                    crm.get('lead_status', 'Open')
                ),
                key=f"status_edit_{lead_idx}"
            )

            # Lead Owner
            new_owner = st.text_input(
                "Lead Owner",
                value=crm.get('lead_owner', ''),
                key=f"owner_edit_{lead_idx}"
            )

            # Last Interaction Date
            current_interaction = crm.get('last_interaction_date')
            if current_interaction:
                try:
                    current_date = datetime.fromisoformat(current_interaction).date()
                except:
                    current_date = None
            else:
                current_date = None

            new_interaction_date = st.date_input(
                "Last Interaction Date",
                value=current_date,
                key=f"interaction_edit_{lead_idx}"
            )

            # Notes
            st.markdown("#### 📝 Notes")
            new_notes = st.text_area(
                "Free-form notes",
                value=crm.get('notes', ''),
                height=200,
                key=f"notes_edit_{lead_idx}"
            )

            # Save Button
            if st.button("💾 Save Changes", key=f"save_lead_{lead_idx}", type="primary"):
                if original_idx is not None:
                    # Update CRM data
                    data['leads'][original_idx]['crm_data']['lead_status'] = new_status
                    data['leads'][original_idx]['crm_data']['lead_owner'] = new_owner
                    data['leads'][original_idx]['crm_data']['last_interaction_date'] = (
                        new_interaction_date.isoformat() if new_interaction_date else None
                    )
                    data['leads'][original_idx]['crm_data']['notes'] = new_notes

                    save_leads(data)
                    st.success("✅ Lead updated successfully!")
                    st.rerun()


if __name__ == "__main__":
    main()
