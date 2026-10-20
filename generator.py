import os
import json
import csv
from openai import OpenAI

# Initialize OpenAI client
# Correct way (reads securely from environment variables)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def passes_icp_filter(lead: dict) -> bool:
    """
    ICP (Ideal Customer Profile) Filter Rules:
    - Must have at least a 4.0 rating
    - Must have at least 20 reviews (proves they are established)
    """
    try:
        rating = float(lead.get('rating', 0))
        reviews = int(lead.get('reviews_count', 0))
        
        if rating >= 4.0 and reviews >= 20:
            return True
        return False
    except ValueError:
        return False

def enrich_and_personalize_lead(lead_data: dict, sender_value_prop: str) -> dict:
    prompt = f"""
    You are an elite B2B growth marketer. Analyze the following target lead data and craft a hyper-personalized cold outreach email.
    
    Target Company Data:
    - Company Name: {lead_data.get('company_name')}
    - Category/Industry: {lead_data.get('category')}
    - Website Text Summary: {lead_data.get('website_summary')}
    - Location: {lead_data.get('location')}
    - Rating/Reviews: {lead_data.get('rating')} ({lead_data.get('reviews_count')} reviews)
    
    Our Value Proposition:
    {sender_value_prop}
    
    Task:
    1. Extract firmographic insights (estimated size, key pain point based on their reviews/website summary).
    2. Write a short, punchy, non-spammy cold email (under 125 words) referencing a specific detail about their business.
    
    Return output strictly as a JSON object with the following keys:
    - "inferred_pain_point": string
    - "email_subject": string
    - "email_body": string
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return {**lead_data, **result}
    except Exception as e:
        print(f"Error processing {lead_data.get('company_name')}: {e}")
        return lead_data

if __name__ == "__main__":
    value_proposition = "We help local businesses automate inbound lead response and customer inquiries in under 2 minutes using AI agents."

    # In production, you can replace this list with data fetched from a real API (like Google Places API or Apify)
    raw_incoming_leads = [
        {
            "company_name": "Bad Lead Inc",
            "category": "Consulting",
            "location": "Lagos, Nigeria",
            "rating": 2.5,
            "reviews_count": 4,
            "website_summary": "Brand new startup, no reviews.",
            "recipient_email": "test1@example.com"
        },
        {
            "company_name": "Lagos Premier Logistics",
            "category": "Courier & Delivery",
            "location": "Lagos, Nigeria",
            "rating": 4.7,
            "reviews_count": 85,
            "website_summary": "Established delivery service. Customers complain about manual tracking updates.",
            "recipient_email": "test2@example.com"
        }
    ]

    print("Filtering leads based on ICP rules...")
    qualified_leads = [lead for lead in raw_incoming_leads if passes_icp_filter(lead)]
    print(f"🎯 Filtered: {len(qualified_leads)} out of {len(raw_incoming_leads)} leads passed ICP criteria.")

    processed_leads = []
    for lead in qualified_leads:
        print(f"Processing AI enrichment for: {lead['company_name']}...")
        enriched = enrich_and_personalize_lead(lead, value_proposition)
        processed_leads.append(enriched)

    # Save results
    output_file = "outreach_results.csv"
    fieldnames = ["company_name", "category", "location", "rating", "reviews_count", "website_summary", "recipient_email", "inferred_pain_point", "email_subject", "email_body"]
    
    with open(output_file, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_leads)

    print(f"\n✨ Done! Qualified leads processed and saved to '{output_file}'.")