"""
Research Agent - Uses Exa API to find industry events and companies.

This agent:
1. Searches for relevant trade shows and industry events
2. For each event, finds exhibiting/attending companies
3. Returns structured data for the enrichment agent
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
    Find companies associated with events.

    Args:
        exa: Initialized Exa client
        events: List of event dicts

    Returns:
        List of company dicts with event association
    """
    companies = []
    seen_companies = set()

    # Search for companies in target industries
    company_queries = [
        "large format signage companies vehicle wraps architectural graphics",
        "sign manufacturing companies protective overlaminates",
        "fleet graphics companies durable graphic films",
        "architectural graphics signage manufacturers",
        "ISA Sign Expo exhibitors large format printing",
        "PRINTING United exhibitors wide format graphics",
        "vehicle wrap companies commercial fleet graphics",
        "Avery Dennison graphics solutions signage",
        "3M commercial graphics films signage"
    ]

    for query in company_queries:
        print(f"  Searching: {query[:60]}...")
        results = exa.search(query, num_results=5)

        for result in results:
            company = parse_company_from_result(result, events)
            if company:
                # Use company name as unique identifier
                company_key = company['name'].lower()
                if company_key not in seen_companies:
                    seen_companies.add(company_key)
                    companies.append(company)

    return companies


def parse_company_from_result(result: Dict, events: List[Dict]) -> Dict:
    """
    Extract company information from Exa search result.

    Args:
        result: Exa search result dict
        events: List of events (for association)

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

    # Associate with an event (pick first one as default)
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
