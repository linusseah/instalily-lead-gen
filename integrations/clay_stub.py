"""
Clay API Integration Stub

This is a documented stub showing where the Clay API integration would slot in.
Clay provides waterfall enrichment across 50+ data sources for contact details.

NOT LIVE - For demonstration and future activation only.
"""


def enrich_contact_clay(company_name: str, title: str) -> dict:
    """
    STUB: In production, this calls the Clay API to waterfall-enrich
    contact details across 50+ data sources (email, phone, LinkedIn, etc.).

    Clay API Overview:
    - Waterfall enrichment across 50+ data providers
    - High accuracy contact discovery and verification
    - Email validation and phone number lookup
    - LinkedIn profile matching and verification

    Clay API Documentation: https://clay.com/api
    Endpoint: POST /enrichment/contact

    Request Format:
    {
        "company_name": "Avery Dennison",
        "job_title": "VP Product Development",
        "additional_context": {
            "industry": "Graphics and Signage",
            "location": "United States"
        }
    }

    Response Format:
    {
        "name": "Laura Noll",
        "email": "laura.noll@example.com",
        "phone": "+1-234-567-8900",
        "linkedin_url": "https://www.linkedin.com/in/laura-noll-6388a55/",
        "verified": true,
        "confidence_score": 0.95,
        "source": "ZoomInfo"
    }

    To Activate:
    1. Sign up for Clay API access at https://clay.com
    2. Add CLAY_API_KEY to your .env file
    3. Install Clay Python SDK: pip install clay-python
    4. Replace this stub function with the implementation below:

    Example Implementation:
    ```python
    import os
    from clay import Clay

    def enrich_contact_clay(company_name: str, title: str) -> dict:
        client = Clay(api_key=os.getenv("CLAY_API_KEY"))

        result = client.enrich_contact(
            company_name=company_name,
            job_title=title,
            additional_context={
                "industry": "Graphics and Signage"
            }
        )

        return {
            "name": result.name,
            "email": result.email,
            "phone": result.phone,
            "linkedin_url": result.linkedin_url,
            "verified": result.verified,
            "source": result.source
        }
    ```

    Rate Limits:
    - Varies by Clay pricing tier
    - Free tier: 100 enrichments/month
    - Growth tier: 1,000 enrichments/month
    - Enterprise tier: Custom limits

    Error Handling:
    - Handle 404 (contact not found)
    - Handle 429 (rate limit exceeded)
    - Implement retry logic with exponential backoff
    - Validate email addresses before use
    """
    return {
        "stub": True,
        "message": "Clay API integration pending — would return verified contact details",
        "inputs": {
            "company": company_name,
            "title": title
        },
        "sample_output": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "linkedin_url": "https://www.linkedin.com/in/johndoe",
            "verified": True,
            "confidence_score": 0.92,
            "source": "Clay Waterfall (ZoomInfo → Clearbit → Hunter.io)"
        },
        "next_steps": [
            "Sign up for Clay API access",
            "Add CLAY_API_KEY to .env",
            "Replace stub with live implementation",
            "Test with sample company/title combinations",
            "Implement error handling and rate limiting"
        ]
    }


if __name__ == "__main__":
    # Test the stub
    result = enrich_contact_clay("Avery Dennison Graphics Solutions", "VP Product Development")
    print("Clay API Stub Response:")
    print(f"Status: {'STUB' if result['stub'] else 'LIVE'}")
    print(f"Message: {result['message']}")
    print(f"\nSample Output:")
    for key, value in result['sample_output'].items():
        print(f"  {key}: {value}")
