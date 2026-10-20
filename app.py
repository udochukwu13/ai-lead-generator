import streamlit as st
import json
import os
import requests
from openai import OpenAI

st.set_page_config(page_title="AI B2B Lead Generator", page_icon="🚀", layout="wide")

st.title("🚀 AI-Powered B2B Lead Generator & Outreach Assistant")
st.markdown("Extract firmographic insights, filter by your ICP, and generate hyper-personalized cold emails instantly.")

# Sidebar configuration
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
apify_token_input = st.sidebar.text_input("Apify API Token (For Live Scraping)", type="password", value="")
value_proposition = st.sidebar.text_area("Your Value Proposition", "We help local businesses automate inbound lead response and customer inquiries in under 2 minutes using AI agents.")

st.sidebar.subheader("ICP Filters")
min_rating = st.sidebar.slider("Minimum Rating", 1.0, 5.0, 4.0)
min_reviews = st.sidebar.number_input("Minimum Reviews Count", value=20)

# Create Tabs for Manual Entry vs. Live Scraper
tab1, tab2 = st.tabs(["✍️ Manual Lead Entry", "🌍 Live Google Maps Scraper"])

with tab1:
    st.subheader("Add Target Lead Details Manually")
    col1, col2 = st.columns(2)

    with col1:
        company_name = st.text_input("Company Name", "Lagos Premier Logistics")
        category = st.text_input("Category / Industry", "Courier & Delivery")
        location = st.text_input("Location", "Lagos, Nigeria")

    with col2:
        rating = st.number_input("Google Rating", value=4.7, min_value=1.0, max_value=5.0)
        reviews_count = st.number_input("Reviews Count", value=85)

    website_summary = st.text_area("Website Summary / Recent Reviews Context", "Established delivery service. Customers frequently complain about slow manual tracking updates and missed delivery notifications.")

    if st.button("Generate Personalized Outreach 🚀"):
        if not api_key_input:
            st.error("Please enter your OpenAI API key in the sidebar.")
        elif rating < min_rating or reviews_count < min_reviews:
            st.warning(f"⚠️ Lead filtered out! Failed ICP criteria (Rating: {rating}, Reviews: {reviews_count}).")
        else:
            client = OpenAI(api_key=api_key_input)
            
            prompt = f"""
            You are an elite B2B growth marketer. Analyze the following target lead data and craft a hyper-personalized cold outreach email.
            
            Target Company Data:
            - Company Name: {company_name}
            - Category/Industry: {category}
            - Website Text Summary: {website_summary}
            - Location: {location}
            - Rating/Reviews: {rating} ({reviews_count} reviews)
            
            Our Value Proposition:
            {value_proposition}
            
            Task:
            1. Extract firmographic insights (estimated size, key pain point based on their reviews/website summary).
            2. Write a short, punchy, non-spammy cold email (under 125 words) referencing a specific detail about their business.
            
            Return output strictly as a JSON object with the following keys:
            - "inferred_pain_point": string
            - "email_subject": string
            - "email_body": string
            """

            with st.spinner("Analyzing lead with AI..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        response_format={"type": "json_object"}
                    )
                    result = json.loads(response.choices[0].message.content)
                    
                    st.success("Lead successfully analyzed and email generated!")
                    st.markdown("### 📊 AI Analysis Results")
                    st.info(f"**Inferred Pain Point:** {result.get('inferred_pain_point')}")
                    
                    st.markdown("### ✉️ Generated Cold Email")
                    st.text_input("Subject Line", result.get('email_subject'))
                    st.text_area("Email Body", result.get('email_body'), height=200)
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")

with tab2:
    st.subheader("Scrape Live Businesses from Google Maps")
    st.markdown("Enter a search query and location to pull real businesses using Apify's web API.")
    
    search_query = st.text_input("Search Query (e.g., Roofing Contractors, Dental Clinics)", "Roofing Contractors")
    search_location = st.text_input("Search Location", "Austin, TX")
    max_results = st.slider("Max Leads to Fetch", 1, 10, 3)

    if st.button("Start Live Scraping 🔍"):
        if not apify_token_input:
            st.error("Please enter your Apify API Token in the sidebar to run live scrapes.")
        else:
            with st.spinner("Calling Apify API to fetch live data..."):
                try:
                    # Trigger Apify Google Maps Scraper Actor via REST API
                    actor_id = "nwua9Gu5YrADL7ZDj"
                    url = f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items?token={apify_token_input}"
                    
                    payload = {
                        "searchStringsArray": [f"{search_query} in {search_location}"],
                        "maxCrawledPlacesPerSearch": max_results,
                        "language": "en"
                    }

                    response = requests.post(url, json=payload, timeout=120)
                    
                    if response.status_code == 201 or response.status_code == 200:
                        items = response.json()
                        scraped_leads = []
                        
                        for item in items:
                            scraped_leads.append({
                                "company_name": item.get("title"),
                                "category": item.get("categoryName"),
                                "location": item.get("address"),
                                "rating": item.get("totalScore", 0),
                                "reviews_count": item.get("reviewsCount", 0),
                                "website_summary": f"Google Maps listing for {item.get('title')} in {search_location}. Website: {item.get('website', 'None')}"
                            })

                        st.success(f"Successfully scraped {len(scraped_leads)} live leads!")
                        st.write(scraped_leads)
                    else:
                        st.error(f"Apify API returned error status {response.status_code}: {response.text}")
                        
                except Exception as e:
                    st.error(f"Scraping failed: {e}")