import requests
import json
import time
import resend

def generate_outreach_email(company_name, industry, rating, reviews_count, location, audit_score, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    prompt = f"""
    Write a short, highly personalized B2B cold outreach email to the owner or manager of {company_name}, a {industry} business in {location}.
    Their Google rating is {rating} stars with {reviews_count} reviews, and their website SEO Health Score is {audit_score}/100.
    Pitching JEdge Connect web optimization, automation, or software solutions to help them fix their online gaps and scale.
    Keep it professional, friendly, and concise.
    """
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    res_json = response.json()
    return res_json["choices"][0]["message"]["content"]

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
    return res_json["choices"][0]["message"]["content"]

def send_outreach_email(to_email, subject, body, api_key):
    resend.api_key = api_key
    params = {
        "from": "JEdge Connect <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": f"<div style='font-family: Arial, sans-serif;'>{body.replace(chr(10), '<br>')}</div>",
    }
    try:
        email_response = resend.Emails.send(params)
        return {"success": True, "id": email_response.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_website_health(url):
    """Audits website SSL, Title tags, Meta descriptions, and load speed with robust headers"""
    if not url or url == 'N/A':
        return {"status": "No Website", "https": False, "has_title": False, "has_description": False, "load_time": "N/A", "score": 0}
    
    is_https = url.startswith("https") or not url.startswith("http")
    
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        start_time = time.time()
        # Use a realistic browser User-Agent to avoid getting blocked by corporate firewalls
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
        load_time = round(time.time() - start_time, 2)
        
        # If site blocks automated scraping with 403/401 but is online
        if response.status_code in [403, 401, 999]:
            return {
                "status": f"Protected (HTTP {response.status_code})",
                "https": is_https,
                "has_title": True,
                "has_description": True,
                "load_time": f"{load_time}s",
                "score": 80
            }
            
        if response.status_code == 200:
            text_lower = response.text.lower()
            has_title = "<title>" in text_lower
            has_description = 'meta name="description"' in text_lower or "meta name='description'" in text_lower
            
            score = 40
            if is_https: score += 20
            if has_title: score += 20
            if has_description: score += 20
            
            return {
                "status": "Online",
                "https": is_https,
                "has_title": has_title,
                "has_description": has_description,
                "load_time": f"{load_time}s",
                "score": score
            }
        else:
            return {
                "status": f"Error {response.status_code}",
                "https": is_https,
                "has_title": False,
                "has_description": False,
                "load_time": f"{load_time}s",
                "score": 40
            }
    except Exception:
        return {
            "status": "Blocked / Unreachable", 
            "https": is_https, 
            "has_title": False, 
            "has_description": False, 
            "load_time": "N/A", 
            "score": 30
        }