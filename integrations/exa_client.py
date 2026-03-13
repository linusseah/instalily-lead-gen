"""
Exa API client wrapper for semantic search.
"""

import os
from typing import List, Dict
from exa_py import Exa


class ExaClient:
    """Wrapper for Exa API semantic search."""

    def __init__(self):
        api_key = os.getenv("EXA_API_KEY")
        if not api_key:
            raise ValueError("EXA_API_KEY not found in environment")
        self.client = Exa(api_key=api_key)

    def search(
        self,
        query: str,
        num_results: int = 10,
        type: str = "neural"
    ) -> List[Dict]:
        """
        Perform semantic search with Exa.

        Args:
            query: Natural language search query
            num_results: Number of results to return
            use_autoprompt: Let Exa optimize the query
            type: Search type ('neural' or 'keyword')

        Returns:
            List of search results with title, url, and text
        """
        try:
            response = self.client.search_and_contents(
                query=query,
                num_results=num_results,
                type=type,
                text=True
            )

            results = []
            for result in response.results:
                results.append({
                    "title": result.title,
                    "url": result.url,
                    "text": result.text[:500] if result.text else "",  # Truncate for brevity
                    "score": getattr(result, 'score', None)
                })

            return results

        except Exception as e:
            print(f"Exa search error: {e}")
            return []

    def get_company_details(self, company_name: str, company_url: str = None) -> Dict:
        """
        Use Exa to gather detailed company information.

        Searches for:
        - Company overview/about page
        - Leadership/team pages
        - Revenue and size information

        Args:
            company_name: Name of the company
            company_url: Optional known URL to focus search

        Returns:
            Dict with company details and decision-maker info
        """
        try:
            # Search for company overview and leadership
            queries = [
                f"{company_name} company about overview",
                f"{company_name} leadership team executives",
                f"{company_name} contact VP director decision maker"
            ]

            all_results = []
            for query in queries:
                results = self.search(query, num_results=3, type="neural")
                all_results.extend(results)

            # Deduplicate by URL
            seen_urls = set()
            unique_results = []
            for result in all_results:
                if result["url"] not in seen_urls:
                    seen_urls.add(result["url"])
                    unique_results.append(result)

            return {
                "company_name": company_name,
                "search_results": unique_results[:5],  # Top 5 unique results
                "website": company_url
            }

        except Exception as e:
            print(f"Error getting company details: {e}")
            return {"company_name": company_name, "search_results": [], "website": company_url}
