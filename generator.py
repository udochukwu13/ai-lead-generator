import requests
import json

def generate_outreach_email(company_name, industry, rating, reviews_count, location, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = f"""
    Write a short, highly personalized B2B cold outreach email to the owner or manager of {company_name}, a {industry} business located in {location}.
    Their Google rating is {rating} stars with {reviews_count} reviews.
    Pitching JEdge Connect services (software solutions, automation, or delivery/payroll solutions like Splitify/JE-Express) to help them scale and improve customer satisfaction.
    Keep it professional, friendly, and concise.
    """
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    res_json = response.json()
    return res_json["choices"]["message"]["content"]

def generate_followup_email(company_name, industry, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = f"""
    Write a short, polite, and friendly follow-up B2B email for {company_name}, a {industry} business. 
    This is a second touchpoint after an initial cold email went unanswered. 
    Keep it brief, value-focused, and give them a very low-friction call to action to reply or chat on WhatsApp.
    """
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    res_json = response.json()
    return res_json["choices"]["message"]["content"]