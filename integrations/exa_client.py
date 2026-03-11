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
        use_autoprompt: bool = True,
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
                use_autoprompt=use_autoprompt,
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
