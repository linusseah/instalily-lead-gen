"""
Research Agent - REWRITTEN with ICP-first strategy.

NEW STRATEGY:
Instead of starting with events and trying to find exhibitors (which returns garbage),
we start with REFERENCE COMPANIES that match the ICP, then use Exa's find_similar()
to discover similar companies. Claude then extracts clean company names.

Two-pronged approach:
1. ICP Similarity Search (primary): Use find_similar() with reference company URLs
2. ICP Keyword Search (backup): Semantic search for companies matching ICP criteria

Output: Clean list of {company_name, website} - NO events, NO decision-makers.
Those are handled by Enrichment Agent phases.
"""

import os
import sys
from typing import List, Dict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.exa_client import ExaClient
from integrations.claude_client import ClaudeClient


# Reference companies that match Tedlar ICP perfectly
REFERENCE_COMPANY_URLS = [
    "https://www.averydennison.com/en/us/products-and-solutions/graphics-solutions.html",
    "https://www.orafol.com/en/products/vehicle-wraps/",
    "https://www.arlon.com/graphics-media/",
    "https://www.fdcfilms.com/",
    "https://www.3m.com/3M/en_US/graphics-signage-us/",
]

# ICP keyword searches as backup strategy
ICP_KEYWORD_QUERIES = [
    "large format signage manufacturers companies",
    "vehicle wrap film producers suppliers",
    "architectural graphics solutions companies",
    "fleet graphics protective films manufacturers",
    "commercial signage overlaminate suppliers",
    "durable graphic films weather resistant manufacturers",
]


def run_research() -> Dict:
    """
    Main entry point for the research agent.

    NEW FLOW:
    1. Use find_similar() on reference company URLs → get similar companies
    2. Use ICP keyword searches → get companies matching ICP criteria
    3. Pass all Exa results to Claude → extract real company names
    4. Deduplicate → return clean company list

    Returns:
        Dict with 'companies' key (list of {company_name, website})
    """
    print("Initializing Exa client...")
    exa = ExaClient()

    print("Initializing Claude client...")
    claude = ClaudeClient()

    # Step 1: Find companies similar to reference ICPs
    print("\n=== STRATEGY 1: ICP Similarity Search ===")
    similarity_results = find_similar_companies(exa)
    print(f"Found {len(similarity_results)} results from similarity search")

    # Step 2: Find companies via ICP keyword searches
    print("\n=== STRATEGY 2: ICP Keyword Search ===")
    keyword_results = find_companies_by_keywords(exa)
    print(f"Found {len(keyword_results)} results from keyword search")

    # Step 3: Combine all results and extract companies with Claude
    print("\n=== EXTRACTING COMPANIES WITH CLAUDE ===")
    all_results = similarity_results + keyword_results
    print(f"Total search results to process: {len(all_results)}")

    companies = extract_companies_with_claude(claude, all_results)
    print(f"✓ Extracted {len(companies)} valid companies")

    # Step 4: Deduplicate by domain
    print("\n=== DEDUPLICATING ===")
    unique_companies = deduplicate_companies(companies)
    print(f"✓ {len(unique_companies)} unique companies after deduplication")

    return {
        "companies": unique_companies
    }


def find_similar_companies(exa: ExaClient) -> List[Dict]:
    """
    Use Exa's find_similar() API to discover companies similar to reference ICPs.

    Args:
        exa: Initialized Exa client

    Returns:
        List of Exa search results
    """
    all_results = []

    for url in REFERENCE_COMPANY_URLS:
        # Extract company name from URL for logging
        company_hint = url.split("//")[1].split("/")[0].replace("www.", "")
        print(f"  Finding companies similar to: {company_hint}")

        results = exa.find_similar(
            url=url,
            num_results=10,
            exclude_source_domain=True  # Don't include the reference company itself
        )

        all_results.extend(results)

    return all_results


def find_companies_by_keywords(exa: ExaClient) -> List[Dict]:
    """
    Use ICP keyword searches to find companies matching Tedlar's target criteria.

    Args:
        exa: Initialized Exa client

    Returns:
        List of Exa search results
    """
    all_results = []

    for query in ICP_KEYWORD_QUERIES:
        print(f"  Searching: {query[:60]}...")

        results = exa.search(
            query=query,
            num_results=8,
            type="neural"
        )

        all_results.extend(results)

    return all_results


def extract_companies_with_claude(claude: ClaudeClient, search_results: List[Dict]) -> List[Dict]:
    """
    Use Claude to extract REAL company names and websites from Exa search results.

    Claude filters out:
    - News articles and blog posts
    - Industry aggregators and directories
    - Social media profiles
    - Event announcements
    - Generic page titles (About Us, Team, etc.)
    - Person names

    Args:
        claude: Initialized Claude client
        search_results: List of Exa search results

    Returns:
        List of {company_name, website} dicts
    """
    # Process in batches of 20 to avoid token limits
    BATCH_SIZE = 20
    all_companies = []

    for i in range(0, len(search_results), BATCH_SIZE):
        batch = search_results[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(search_results) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} results)...")

        companies = claude.extract_companies_from_search_results(batch)
        print(f"    → Extracted {len(companies)} companies from batch")

        all_companies.extend(companies)

    return all_companies


def deduplicate_companies(companies: List[Dict]) -> List[Dict]:
    """
    Deduplicate companies by domain.

    If two companies have the same domain, keep the first one.

    Args:
        companies: List of {company_name, website} dicts

    Returns:
        Deduplicated list
    """
    seen_domains = set()
    unique_companies = []

    for company in companies:
        website = company.get("website", "")

        # Extract domain from URL
        try:
            # Remove protocol
            domain = website.replace("https://", "").replace("http://", "")
            # Remove www.
            domain = domain.replace("www.", "")
            # Take just the domain (before first /)
            domain = domain.split("/")[0]

            if domain and domain not in seen_domains:
                seen_domains.add(domain)
                unique_companies.append(company)
        except:
            # If we can't parse the URL, keep it anyway
            unique_companies.append(company)

    return unique_companies


if __name__ == "__main__":
    # Test the research agent
    results = run_research()
    print("\n" + "=" * 80)
    print(f"Research complete: {len(results['companies'])} companies found")
    print("\nSample companies:")
    for company in results['companies'][:5]:
        print(f"  - {company['company_name']}: {company['website']}")
