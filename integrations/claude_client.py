"""
Claude API client for structured extraction and enrichment tasks.
"""

import os
from typing import List, Dict
import json
from anthropic import Anthropic


class ClaudeClient:
    """Wrapper for Claude API for extraction and enrichment."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-6"  # Latest model

    def extract_companies_from_search_results(self, search_results: List[Dict]) -> List[Dict]:
        """
        Use Claude to extract real company names and websites from Exa search results.

        This filters out:
        - News articles and blog posts
        - Industry aggregators
        - LinkedIn and social media profiles
        - Event announcements
        - Generic "About Us" or "Team" pages

        Args:
            search_results: List of Exa search results (title, url, text)

        Returns:
            List of {company_name, website} dicts
        """
        # Format search results for Claude
        formatted_results = []
        for i, result in enumerate(search_results, 1):
            formatted_results.append(f"""
Result {i}:
Title: {result.get('title', 'N/A')}
URL: {result.get('url', 'N/A')}
Text: {result.get('text', 'N/A')[:300]}...
""")

        results_text = "\n".join(formatted_results)

        prompt = f"""You are analyzing search results to extract REAL COMPANY NAMES and their websites for a B2B lead generation pipeline.

Search results to analyze:
{results_text}

CRITICAL FILTERING RULES:
1. ONLY extract results that are clearly COMPANY WEBSITES (not news articles, blogs, aggregators, or social media)
2. EXCLUDE:
   - News articles (titles with "unveils", "announces", "confirms", "to host", etc.)
   - Industry blogs and media sites (print21.com, signanddigital.com, etc.)
   - LinkedIn profiles, Facebook pages, Twitter
   - Event announcements and conference listings
   - Aggregator sites (exhibitor lists, directories, association pages)
   - Generic page titles like "About Us", "Team", "Leadership", "Contact"
   - Person names (e.g., "John Smith", "Thomas J. Quinlan III")
   - FESPA, ISA, PRINTING United (these are associations, not companies)

3. ONLY INCLUDE:
   - Direct company websites (example.com, not news-site.com/article-about-example)
   - Company product/service pages
   - Results where the URL domain matches the company name

For each VALID company you find, extract:
- company_name: The actual company name (NOT a page title, NOT a person name)
- website: The root domain URL (e.g., https://example.com, not https://example.com/about/team)

Return ONLY a JSON array of companies:
[
  {{"company_name": "Example Corp", "website": "https://example.com"}},
  {{"company_name": "Another Company", "website": "https://another.com"}}
]

If NO valid companies are found in these results, return an empty array: []

Do NOT include explanations. Return ONLY the JSON array."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            # Parse JSON
            companies = json.loads(response_text)

            if not isinstance(companies, list):
                print(f"  ⚠ Claude returned non-list response, skipping batch")
                return []

            return companies

        except json.JSONDecodeError as e:
            print(f"  ⚠ Claude response was not valid JSON: {e}")
            print(f"  Response: {response_text[:200]}")
            return []
        except Exception as e:
            print(f"  ⚠ Claude extraction error: {e}")
            return []


if __name__ == "__main__":
    # Test the Claude client
    from dotenv import load_dotenv
    load_dotenv()

    client = ClaudeClient()
    print("✓ Claude client initialized successfully")

    # Test with sample search results
    sample_results = [
        {
            "title": "Avery Dennison Graphics Solutions",
            "url": "https://www.averydennison.com/en/us/products-and-solutions/graphics-solutions.html",
            "text": "Avery Dennison is a global leader in pressure-sensitive materials and graphic solutions..."
        },
        {
            "title": "FESPA Global unveils exhibitor lineup",
            "url": "https://www.fespa.com/news/article/fespa-global-unveils-exhibitor-lineup",
            "text": "FESPA has announced the full exhibitor list for the upcoming trade show..."
        }
    ]

    companies = client.extract_companies_from_search_results(sample_results)
    print(f"✓ Extracted {len(companies)} companies:")
    for company in companies:
        print(f"  - {company['company_name']}: {company['website']}")
