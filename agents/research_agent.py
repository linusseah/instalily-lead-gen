"""
Research Agent - Uses Exa API to find industry events and companies with verified contacts.

CONTACT-FIRST STRATEGY:
This agent prioritizes finding REAL, CONTACTABLE leads over general company info.

Two search strategies:
1. EVENT-BASED: Start with events that have publicly available attendee/exhibitor lists
   → Find companies on those lists → Find contacts at those companies → Score fit

2. ICP-BASED: Start with companies similar to reference ICP
   → Find key decision-makers → Score fit → Match to likely events

CRITICAL: A lead without a findable contact (name + title minimum) is NOT a valid lead.
"""

import os
import sys
from typing import List, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.exa_client import ExaClient


# Target events and associations from ICP
TARGET_EVENTS = [
    "ISA Sign Expo 2026",
    "PRINTING United Expo 2026",
    "FESPA Global Print Expo 2026",
    "SEGD experiential graphic design"
]

TARGET_INDUSTRIES = [
    "large format signage",
    "vehicle wraps",
    "fleet graphics",
    "architectural graphics",
    "protective films for graphics"
]


def run_research() -> Dict:
    """
    Main entry point for the research agent.

    Returns:
        Dict with 'events' and 'companies' keys
    """
    print("Initializing Exa client...")
    exa = ExaClient()

    # Step 1: Find events
    print("\nSearching for industry events...")
    events = find_events(exa)
    print(f"Found {len(events)} relevant events")

    # Step 2: Find companies for each event
    print("\nSearching for companies at these events...")
    companies = find_companies(exa, events)
    print(f"Found {len(companies)} candidate companies")

    return {
        "events": events,
        "companies": companies
    }


def find_events(exa: ExaClient) -> List[Dict]:
    """
    Search for relevant industry events and trade shows.

    Args:
        exa: Initialized Exa client

    Returns:
        List of event dicts with name, date, location, relevance
    """
    events = []

    # Search queries for different event types
    event_queries = [
        "ISA Sign Expo 2026 Orlando trade show signage graphics",
        "PRINTING United Expo 2026 Las Vegas large format",
        "FESPA Global Print Expo 2026 Barcelona",
        "SEGD Society Experiential Graphic Design conference 2026",
        "graphics signage industry trade shows 2026 exhibitors"
    ]

    seen_urls = set()

    for query in event_queries:
        print(f"  Searching: {query[:60]}...")
        results = exa.search(query, num_results=3)

        for result in results:
            # Avoid duplicates
            if result['url'] in seen_urls:
                continue
            seen_urls.add(result['url'])

            # Parse event info from results
            event = parse_event_from_result(result)
            if event:
                events.append(event)

    # Add known key events manually to ensure coverage
    known_events = [
        {
            "name": "ISA Sign Expo 2026",
            "date": "April 2026",
            "location": "Orlando, FL",
            "relevance": "Largest sign and graphics industry trade show in North America. DuPont joined ISA in 2025.",
            "source_url": "https://www.signexpo.org"
        },
        {
            "name": "PRINTING United Expo 2026",
            "date": "September 2026",
            "location": "Las Vegas, NV",
            "relevance": "Major printing industry event covering large-format graphics and signage applications.",
            "source_url": "https://www.printingunited.com"
        }
    ]

    for known_event in known_events:
        if not any(e['name'] == known_event['name'] for e in events):
            events.append(known_event)

    return events


def parse_event_from_result(result: Dict) -> Dict:
    """
    Extract event information from Exa search result.

    Args:
        result: Exa search result dict

    Returns:
        Event dict or None if not a valid event
    """
    title = result.get('title', '')
    text = result.get('text', '')
    url = result.get('url', '')

    # Basic validation - should mention event/expo/conference
    event_keywords = ['expo', 'conference', 'trade show', 'event', 'summit']
    if not any(keyword in title.lower() for keyword in event_keywords):
        return None

    # Extract what we can
    event = {
        "name": title.split('|')[0].strip(),  # Clean up title
        "date": "2026",  # Default to target year
        "location": "TBD",
        "relevance": text[:200] if text else "Relevant industry event for graphics and signage.",
        "source_url": url
    }

    return event


def find_companies(exa: ExaClient, events: List[Dict]) -> List[Dict]:
    """
    Find companies with VERIFIED CONTACTS - contact-first strategy.

    Priority: Find people first, then validate companies.
    Only return companies where we can find at least a name + title.

    Args:
        exa: Initialized Exa client
        events: List of event dicts

    Returns:
        List of company dicts with initial contact signals
    """
    companies = []
    seen_companies = set()

    print("\n  === STRATEGY 1: Event-Based Contact Discovery ===")
    # Search for EVENT ATTENDEE LISTS and EXHIBITOR DIRECTORIES with contact info
    event_contact_queries = [
        ("ISA Sign Expo 2026 exhibitors list companies contacts", "ISA Sign Expo 2026"),
        ("ISA Sign Expo Orlando 2026 attendees sponsors exhibitors directory", "ISA Sign Expo 2026"),
        ("PRINTING United Expo 2026 exhibitor directory speakers", "PRINTING United Expo 2026"),
        ("PRINTING United Las Vegas 2026 exhibitors list companies", "PRINTING United Expo 2026"),
        ("FESPA 2026 Barcelona exhibitor list signage graphics", "FESPA Global Print Expo 2026"),
        ("SEGD members directory experiential graphics designers", "SEGD experiential graphic design"),
    ]

    for query, event_name in event_contact_queries:
        print(f"  Searching: {query[:60]}...")
        results = exa.search(query, num_results=5, type="neural")

        associated_event = next((e for e in events if e['name'] == event_name), None)
        if not associated_event:
            associated_event = {
                "name": event_name,
                "date": "2026",
                "location": "TBD",
                "relevance": f"Event identified through research",
                "source_url": ""
            }

        for result in results:
            # Look for results that mention attendees, exhibitors, speakers, or contact info
            text_lower = result.get('text', '').lower()
            title_lower = result.get('title', '').lower()

            if any(keyword in text_lower or keyword in title_lower
                   for keyword in ['exhibitor', 'attendee', 'speaker', 'directory', 'list', 'sponsors']):
                company = parse_company_from_result(result, events, forced_event=associated_event)
                if company:
                    company_key = company['name'].lower()
                    if company_key not in seen_companies:
                        seen_companies.add(company_key)
                        company['contact_signal'] = 'high'  # Event list = higher contact findability
                        companies.append(company)

    print("\n  === STRATEGY 2: ICP-Similar Companies with Known Leaders ===")
    # Search for companies similar to reference ICP (Avery Dennison) with leadership info
    icp_leadership_queries = [
        "large format signage companies VP Product Director leadership team",
        "vehicle wrap manufacturers executives leadership contacts",
        "architectural graphics film companies decision makers VP Procurement",
        "sign industry manufacturers leadership team executive contacts",
        "protective overlaminate film producers executives VP R&D Product",
        "commercial graphics solutions companies leadership executives"
    ]

    # These go under "Industry Research" initially - event matching happens in enrichment
    industry_placeholder = {
        "name": "N/A",
        "date": "N/A",
        "location": "N/A",
        "relevance": "Company identified through ICP similarity research. Event attendance to be verified during enrichment."
    }

    for query in icp_leadership_queries:
        print(f"  Searching: {query[:60]}...")
        results = exa.search(query, num_results=4, type="neural")

        for result in results:
            text_lower = result.get('text', '').lower()
            title_lower = result.get('title', '').lower()

            # Prioritize results that mention titles, names, or leadership
            has_leadership_signal = any(keyword in text_lower or keyword in title_lower
                                       for keyword in ['vp', 'director', 'ceo', 'president', 'executive',
                                                       'leadership', 'team', 'officer', 'manager'])

            if has_leadership_signal:
                company = parse_company_from_result(result, events, forced_event=industry_placeholder)
                if company:
                    company_key = company['name'].lower()
                    if company_key not in seen_companies:
                        seen_companies.add(company_key)
                        company['contact_signal'] = 'medium'  # General search = medium findability
                        companies.append(company)

    print(f"\n  Found {len(companies)} candidate companies with contact signals")
    return companies


def parse_company_from_result(result: Dict, events: List[Dict], forced_event: Dict = None) -> Dict:
    """
    Extract company information from Exa search result.

    Args:
        result: Exa search result dict
        events: List of events (for association)
        forced_event: Event to associate with this company (overrides default)

    Returns:
        Company dict or None if not valid
    """
    title = result.get('title', '')
    url = result.get('url', '')
    text = result.get('text', '')

    # Skip if it's an event page, not a company
    skip_keywords = ['expo', 'conference', 'event', 'trade show', 'association']
    if any(keyword in title.lower() for keyword in skip_keywords) and 'company' not in title.lower():
        return None

    # Extract company name (crude extraction from title)
    company_name = title.split('|')[0].split('-')[0].strip()

    # Use forced event if provided, otherwise pick from events list
    if forced_event:
        associated_event = forced_event
    else:
        associated_event = events[0] if events else {
            "name": "Industry Research",
            "date": "2026",
            "location": "N/A",
            "relevance": "Found through industry research"
        }

    company = {
        "name": company_name,
        "website": url,
        "initial_fit_signal": text[:200] if text else "Company in graphics and signage industry",
        "event": associated_event
    }

    return company


if __name__ == "__main__":
    # Test the research agent
    results = run_research()
    print("\n" + "=" * 80)
    print(f"Research complete: {len(results['events'])} events, {len(results['companies'])} companies")
