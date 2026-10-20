import os
import streamlit as st
from openai import OpenAI

# Safely fetch OpenAI key from Streamlit Secrets or environment fallback
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")

client = OpenAI(api_key=openai_api_key)

def generate_outreach_email(company_name, industry, rating, reviews_count, location, api_key=None):
    # Use passed api_key (from sidebar) or fallback to the master secret key
    active_key = api_key if api_key else openai_api_key
    
    if not active_key:
        raise ValueError("Missing OpenAI API Key. Please configure it in Streamlit Secrets.")

    # Re-initialize client with active key if needed
    local_client = OpenAI(api_key=active_key)
    
    prompt = f"""
    Write a hyper-personalized B2B cold email for a company named {company_name}.
    Industry: {industry}
    Location: {location}
    Google Rating: {rating} ({reviews_count} reviews)
    
    The email should pitch automated lead generation services to help them get more clients. Keep it concise, engaging, and professional.
    """
    
    response = local_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content