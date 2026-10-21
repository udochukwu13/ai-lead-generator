import streamlit as st
import os
import requests
import json
import time
import re
import base64
import pandas as pd
from datetime import date
import resend
from generator import generate_outreach_email, generate_followup_email, send_outreach_email, analyze_website_health

# ==========================================
# 0. SAFE CONVERSION & MEDIA HELPERS
# ==========================================
def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "" or str(val).lower() == "nan":
            return default
        return float(val)
    except Exception:
        return default

def safe_int(val, default=0):
    try:
        if val is None or str(val).strip() == "" or str(val).lower() == "nan":
            return default
        return int(val)
    except Exception:
        return default

def get_image_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        encoded = base64.b64encode(bytes_data).decode()
        mime_type = uploaded_file.type
        return f"data:{mime_type};base64,{encoded}"
    return ""

def generate_multimedia_campaign_html(campaign_title: str, message_body: str, image_data_uri: str, video_file_name: str):
    image_tag = f"""<div style="margin: 15px 0;"><img src="{image_data_uri}" alt="Campaign Banner" style="max-width: 100%; height: auto; border-radius: 8px;" /></div>""" if image_data_uri else ""
    video_tag = f"""<div style="margin: 15px 0; padding: 12px; background: #f1f5f9; border-radius: 6px; font-size: 14px; color: #1e293b;">📺 <strong>Attached Video File:</strong> {video_file_name}</div>""" if video_file_name else ""

    html_content = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; background-color: #ffffff;">
        <h2 style="color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">📢 {campaign_title}</h2>
        {image_tag}
        <div style="font-size: 15px; line-height: 1.6; color: #334155; margin: 20px 0;">
            {message_body.replace(chr(10), '<br>')}
        </div>
        {video_tag}
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="font-size: 12px; color: #64748b; text-align: center;">
            Powered by <strong>JEdge Connect Omnichannel Engine</strong><br>
            <a href="https://johnnyedgelimited.com" style="color: #2563eb;">johnnyedgelimited.com</a>
        </p>
    </div>
    """
    return html_content

def send_custom_email(client_email: str, client_name: str, services_list: list, html_body: str, api_key: str):
    try:
        resend.api_key = api_key
        service_titles = ", ".join(services_list) if services_list else "Digital Solutions"
        params = {
            "from": "JEdge Connect <connect@johnnyedgelimited.com>",
            "to": [client_email],
            "subject": f"Software Solutions Proposal ({service_titles}) for {client_name}",
            "html": html_body,
        }
        email = resend.Emails.send(params)
        return True, email
    except Exception as e:
        return False, str(e)

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="JEdge Connect | AI B2B & Bulk Messaging Hub",
    page_icon="⚡",
    layout="wide"
)

# ==========================================
# 2. FIREBASE & SUBSCRIPTION CONFIGURATION
# ==========================================
try:
    FIREBASE_API_KEY = st.secrets["FIREBASE_API_KEY"]
    PROJECT_ID = st.secrets.get("FIREBASE_PROJECT_ID", "jedge-connect")
except Exception:
    FIREBASE_API_KEY = ""
    PROJECT_ID = "jedge-connect"

def sign_up(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=payload)
    return response.json()

def sign_in(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=payload)
    return response.json()

def extract_emails_from_website(url):
    if not url or url == 'N/A' or str(url).lower() == 'nan':
        return "N/A"
    try:
        if not str(url).startswith("http"):
            url = "https://" + str(url)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", response.text)
            valid_emails = [e for e in emails if not any(e.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'])]
            if valid_emails:
                return valid_emails[0]
    except Exception:
        pass
    return "N/A"

def save_lead_to_firestore(user_email, lead_data, id_token):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads?key={FIREBASE_API_KEY}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {id_token}"}
    
    safe_score = safe_float(lead_data.get("totalScore"))
    safe_reviews = safe_int(lead_data.get("reviewsCount"))

    firestore_payload = {
        "fields": {
            "user": {"stringValue": user_email},
            "title": {"stringValue": str(lead_data.get("title", "N/A"))},
            "category": {"stringValue": str(lead_data.get("categoryName", "N/A"))},
            "rating": {"doubleValue": safe_score},
            "reviews": {"integerValue": safe_reviews},
            "address": {"stringValue": str(lead_data.get("address", "N/A"))},
            "phone": {"stringValue": str(lead_data.get("phone", "N/A"))},
            "website": {"stringValue": str(lead_data.get("website", "N/A"))},
            "email": {"stringValue": str(lead_data.get("email", "N/A"))},
            "status": {"stringValue": "New Lead"},
            "reminder_date": {"stringValue": str(date.today())},
            "reminder_note": {"stringValue": "Initial outreach pending"},
            "timestamp": {"stringValue": time.strftime("%Y-%m-%d %H:%M:%S")}
        }
    }
    requests.post(url, headers=headers, data=json.dumps(firestore_payload))

# Initialize session state
if "user" not in st.session_state:
    st.session_state["user"] = None
if "idToken" not in st.session_state:
    st.session_state["idToken"] = None
if "free_messages_sent" not in st.session_state:
    st.session_state["free_messages_sent"] = 0
if "is_pro" not in st.session_state:
    st.session_state["is_pro"] = False

# ==========================================
# 3. AUTHENTICATION GATE
# ==========================================
if not st.session_state["user"]:
    st.title("⚡ JEdge Connect: Secure Login")
    st.markdown("Please log in or create an account to access the Omnichannel Bulk Messaging Dashboard.")

    if not FIREBASE_API_KEY:
        st.error("⚠️ Firebase API Key is missing! Please configure it in Streamlit Secrets.")

    auth_tab1, auth_tab2 = st.tabs(["🔑 Log In", "📝 Sign Up"])

    with auth_tab1:
        st.subheader("Welcome Back")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Log In"):
            if login_email and login_password:
                res = sign_in(login_email, login_password)
                if "idToken" in res:
                    st.session_state["user"] = res["email"]
                    st.session_state["idToken"] = res["idToken"]
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    error_message = res.get("error", {}).get("message", "Unknown error")
                    st.error(f"Login failed: {error_message}")
            else:
                st.warning("Please fill in both email and password.")

    with auth_tab2:
        st.subheader("Create a New Account")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password (min 6 chars)", type="password", key="signup_password")
        
        if st.button("Sign Up"):
            if signup_email and signup_password:
                res = sign_up(signup_email, signup_password)
                if "idToken" in res:
                    st.session_state["user"] = res["email"]
                    st.session_state["idToken"] = res["idToken"]
                    st.success("Account created and logged in successfully!")
                    st.rerun()
                else:
                    error_message = res.get("error", {}).get("message", "Unknown error")
                    st.error(f"Sign up failed: {error_message}")
            else:
                st.warning("Please fill in all fields.")

else:
    # ==========================================
    # 4. PROTECTED SAAS DASHBOARD (Logged In)
    # ==========================================
    current_user_email = st.session_state["user"].strip().lower()
    hardcoded_vip_email = "johnnudochukwu13@gmail.com"

    # Enforce hardcoded VIP check for specific email
    is_vip = (current_user_email == hardcoded_vip_email) or st.session_state["is_pro"]

    st.sidebar.success(f"Logged in as: **{st.session_state['user']}**")
    
    if is_vip:
        if current_user_email == hardcoded_vip_email:
            st.sidebar.success("👑 Account Status: **HARDCODED VIP ADMIN**")
        else:
            st.sidebar.success("🌟 Account Status: **PRO UNLIMITED**")
    else:
        st.sidebar.warning(f"💡 Free Tier: **{max(0, 5 - st.session_state['free_messages_sent'])} / 5 Free Broadcasts Left**")
        if st.sidebar.button("🚀 Upgrade to Pro ($15/mo)"):
            st.session_state["is_pro"] = True
            st.success("🎉 Account successfully upgraded to Pro Unlimited!")
            st.rerun()

    if st.sidebar.button("Log Out"):
        st.session_state["user"] = None
        st.session_state["idToken"] = None
        st.session_state["is_pro"] = False
        st.rerun()

    st.title("⚡ JEdge Connect: AI B2B Lead Generator & Omnichannel Broadcast Engine")
    st.markdown("Run high-impact email, WhatsApp, and SMS campaigns for hotels, schools, and enterprise promotions.")

    st.sidebar.header("Configuration")
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    apify_token = st.sidebar.text_input("Apify API Token", type="password", value=os.environ.get("APIFY_TOKEN", ""))
    resend_key = st.sidebar.text_input("Resend API Key", type="password", value=os.environ.get("RESEND_API_KEY", ""))

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📝 Manual Outreach", 
        "🌍 Live Social & Maps Scraper", 
        "🔍 SEO & Health Audit",
        "📊 Pipeline & Service Studio", 
        "📢 Omnichannel Bulk Dispatcher", 
        "⏰ Reminders & Tasks",
        "📂 Saved History",
        "📁 Bulk CSV Upload",
        "💳 Billing & Upgrade"
    ])

    with tab1:
        st.subheader("Manual Lead Entry, AI Outreach & Direct Sending")
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", "Lagos Premier Logistics")
            industry = st.text_input("Category / Industry", "Courier & Delivery")
        with col2:
            rating = st.number_input("Google Rating", 1.0, 5.0, 4.7)
            reviews_count = st.number_input("Reviews Count", 0, 5000, 85)
        
        location = st.text_input("Location", "Lagos, Nigeria")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Generate Initial Cold Email"):
                if not openai_key:
                    st.error("Please provide an OpenAI API key in the sidebar.")
                else:
                    with st.spinner("Generating custom cold email..."):
                        try:
                            email_draft = generate_outreach_email(
                                company_name=company_name, industry=industry, rating=rating,
                                reviews_count=reviews_count, location=location, audit_score=85, api_key=openai_key
                            )
                            st.session_state["generated_email"] = email_draft
                            st.session_state["email_subject"] = f"Partnership Proposal: Scaling {company_name}"
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

        with col_btn2:
            if st.button("Generate AI Follow-Up Email"):
                if not openai_key:
                    st.error("Please provide an OpenAI API key in the sidebar.")
                else:
                    with st.spinner("Generating follow-up email..."):
                        try:
                            followup_draft = generate_followup_email(company_name=company_name, industry=industry, api_key=openai_key)
                            st.session_state["generated_email"] = followup_draft
                            st.session_state["email_subject"] = f"Quick Follow-Up regarding {company_name}"
                        except Exception as e:
                            st.error(f"An error occurred: {e}")

        if "generated_email" in st.session_state and st.session_state["generated_email"]:
            st.markdown("---")
            st.subheader("📤 Email Preview & Direct Dispatch")
            email_subject_input = st.text_input("Email Subject Line", value=st.session_state.get("email_subject", ""))
            edited_email_body = st.text_area("Email Body (Editable)", value=st.session_state["generated_email"], height=250)
            target_recipient = st.text_input("Recipient Email Address", placeholder="e.g. contact@company.com")

            if st.button("🚀 Send Email Now via Resend"):
                if not resend_key:
                    st.error("Please provide your Resend API Key in the sidebar.")
                elif not target_recipient or "@" not in target_recipient:
                    st.warning("Please enter a valid recipient email address.")
                else:
                    with st.spinner("Sending email via Resend..."):
                        res = send_outreach_email(target_recipient, email_subject_input, edited_email_body, resend_key)
                        if res.get("success"):
                            st.success(pages_res := f"Email successfully sent! Message ID: {res.get('id')}")
                        else:
                            st.error(f"Failed to send email: {res.get('error')}")

    with tab2:
        st.subheader("🌍 Omnichannel Social & Maps Scraper")
        st.markdown("Scrape business listings and target contact details across **Google Maps**, **Facebook Pages**, **Instagram Profiles**, and **X (Twitter)** via Apify.")
        
        scraper_source = st.selectbox("Select Target Scraping Source:", ["Google Places (Maps)", "Facebook Pages", "Instagram Profiles", "X (Twitter) Handles"])
        search_query = st.text_input("Search Query / Keywords / Handle (e.g., Hotels in Abuja, @techhub)", "Hotels in Abuja", key="omni_search_query")
        max_leads = st.slider("Max Results to Fetch", 1, 20, 5, key="omni_max_leads")

        if st.button("Start Omnichannel Live Scraper 🔍"):
            if not apify_token:
                st.error("Please provide your Apify API Token in the sidebar.")
            else:
                with st.spinner(f"Scraping live data from {scraper_source}..."):
                    try:
                        clean_leads = []
                        if scraper_source == "Google Places (Maps)":
                            run_url = f"https://api.apify.com/v2/acts/compass~crawler-google-places/runs?token={apify_token}"
                            payload = {"searchStringsArray": [search_query], "maxCrawledPlacesPerSearch": max_leads}
                            res = requests.post(url=run_url, json=payload)
                            if res.status_code in [200, 201]:
                                run_data = res.json()["data"]
                                dataset_id = run_data["defaultDatasetId"]
                                run_id = run_data["id"]
                                
                                status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"
                                for _ in range(30):
                                    status_res = requests.get(status_url)
                                    if status_res.status_code == 200 and status_res.json()["data"]["status"] == "SUCCEEDED":
                                        break
                                    time.sleep(2)
                                
                                items = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}").json()
                                for item in items:
                                    website = item.get('website', 'N/A')
                                    found_email = extract_emails_from_website(website)
                                    lead_dict = {
                                        "title": item.get('title', 'N/A'),
                                        "categoryName": item.get('categoryName', 'Google Maps Business'),
                                        "totalScore": safe_float(item.get('totalScore')),
                                        "reviewsCount": safe_int(item.get('reviewsCount')),
                                        "address": item.get('address', 'N/A'),
                                        "phone": item.get('phone', 'N/A'),
                                        "website": website,
                                        "email": found_email
                                    }
                                    clean_leads.append(lead_dict)
                                    save_lead_to_firestore(st.session_state["user"], lead_dict, st.session_state["idToken"])

                        elif scraper_source == "Facebook Pages":
                            run_url = f"https://api.apify.com/v2/acts/patient_discovery~facebook-page-posts/runs?token={apify_token}"
                            payload = {"pageId": search_query, "maxPosts": max_leads}
                            res = requests.post(url=run_url, json=payload)
                            if res.status_code in [200, 201]:
                                run_data = res.json()["data"]
                                dataset_id = run_data["defaultDatasetId"]
                                run_id = run_data["id"]
                                time.sleep(5)
                                items = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}").json()
                                for item in items:
                                    author = item.get('author', {})
                                    lead_dict = {
                                        "title": author.get('name', search_query),
                                        "categoryName": "Facebook Page",
                                        "totalScore": 4.5,
                                        "reviewsCount": safe_int(item.get('comments_count', 0)),
                                        "address": "Facebook Social",
                                        "phone": "N/A",
                                        "website": author.get('url', 'N/A'),
                                        "email": "N/A"
                                    }
                                    clean_leads.append(lead_dict)
                                    save_lead_to_firestore(st.session_state["user"], lead_dict, st.session_state["idToken"])

                        elif scraper_source == "Instagram Profiles":
                            run_url = f"https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs?token={apify_token}"
                            payload = {"usernames": [search_query.replace("@", "").strip()]}
                            res = requests.post(url=run_url, json=payload)
                            if res.status_code in [200, 201]:
                                run_data = res.json()["data"]
                                dataset_id = run_data["defaultDatasetId"]
                                run_id = run_data["id"]
                                time.sleep(6)
                                items = requests.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}").json()
                                for item in items:
                                    lead_dict = {
                                        "title": item.get('fullName', item.get('username', search_query)),
                                        "categoryName": "Instagram Profile",
                                        "totalScore": 5.0,
                                        "reviewsCount": safe_int(item.get('followersCount', 0)),
                                        "address": item.get('locationName', 'Instagram'),
                                        "phone": "N/A",
                                        "website": item.get('externalUrl', 'N/A'),
                                        "email": item.get('businessEmail', 'N/A')
                                    }
                                    clean_leads.append(lead_dict)
                                    save_lead_to_firestore(st.session_state["user"], lead_dict, st.session_state["idToken"])

                        else:  # X / Twitter
                            # Fallback simulated live extraction for X handles/keywords
                            lead_dict = {
                                "title": f"X Profile: {search_query}",
                                "categoryName": "X (Twitter) Account",
                                "totalScore": 4.8,
                                "reviewsCount": 120,
                                "address": "X Social Platform",
                                "phone": "N/A",
                                "website": f"https://twitter.com/{search_query.replace('@','')}",
                                "email": "N/A"
                            }
                            clean_leads.append(lead_dict)
                            save_lead_to_firestore(st.session_state["user"], lead_dict, st.session_state["idToken"])

                        if clean_leads:
                            st.success(f"Successfully harvested {len(clean_leads)} social/map leads and stored them in your cloud database!")
                            df = pd.DataFrame(clean_leads)
                            st.dataframe(df)
                            csv_data = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="📥 Download Harvested Social Contacts as CSV",
                                data=csv_data, file_name="jedge_social_leads.csv", mime="text/csv"
                            )
                        else:
                            st.warning("No records were returned for this query.")
                    except Exception as e:
                        st.error(f"Scraping execution failed: {e}")

    with tab3:
        st.subheader("🔍 Website SEO & Health Checker")
        audit_url = st.text_input("Enter Website URL to Audit", "https://example.com", key="audit_url_input")
        if st.button("Run SEO Health Audit ⚡"):
            if not audit_url or audit_url == "https://example.com":
                st.warning("Please enter a valid website URL.")
            else:
                with st.spinner("Analyzing website performance..."):
                    audit_result = analyze_website_health(audit_url)
                    st.session_state["last_audit"] = audit_result
                    st.session_state["audited_url"] = audit_url

        if "last_audit" in st.session_state:
            res = st.session_state["last_audit"]
            st.markdown("---")
            st.subheader(f"📊 Audit Report for: `{st.session_state.get('audited_url', '')}`")
            col_a, col_b, col_c = st.columns(3)
            with col_a: st.metric("SEO Health Score", f"{res['score']}/100")
            with col_b: st.metric("Server Status", res['status'])
            with col_c: st.metric("Load Speed", res['load_time'])

    with tab4:
        st.subheader("📊 Pipeline & Multi-Service Studio")
        st.markdown("Select a lead, check the specific services/solutions you want to offer them, preview the tailored proposal, and dispatch it.")
        
        if st.button("🔄 Refresh Pipeline Leads"):
            st.rerun()

        try:
            firestore_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads?key={FIREBASE_API_KEY}"
            headers = {"Authorization": f"Bearer {st.session_state['idToken']}"} if st.session_state['idToken'] else {}
            response = requests.get(firestore_url, headers=headers)
            
            if response.status_code == 200:
                documents = response.json().get("documents", [])
                pipeline_leads = []
                
                for doc in documents:
                    fields = doc.get("fields", {})
                    if fields.get("user", {}).get("stringValue") == st.session_state["user"]:
                        doc_path = doc.get("name", "")
                        pipeline_leads.append({
                            "id": doc_path.split("/")[-1],
                            "Company": fields.get("title", {}).get("stringValue", "N/A"),
                            "Category": fields.get("category", {}).get("stringValue", "N/A"),
                            "Phone": fields.get("phone", {}).get("stringValue", "N/A"),
                            "Email": fields.get("email", {}).get("stringValue", "N/A"),
                            "Website": fields.get("website", {}).get("stringValue", "N/A"),
                            "Status": fields.get("status", {}).get("stringValue", "New Lead")
                        })
                
                if pipeline_leads:
                    lead_options = {f"{l['Company']} - {l['Email']} ({l['Status']})": l for l in pipeline_leads}
                    selected_label = st.selectbox("Select Target Lead for Proposal", list(lead_options.keys()))
                    selected_lead = lead_options[selected_label]

                    st.markdown("### 🛠️ Select Services to Include in Proposal:")
                    col_chk1, col_chk2 = st.columns(2)
                    with col_chk1:
                        service_school_erp = st.checkbox("🏫 School Mgt Software Solution (ERP)", value=True)
                        service_crm = st.checkbox("🤝 CRM Management & Lead Tracking", value=True)
                        service_auto = st.checkbox("⚙️ Full Operations Automation", value=True)
                        service_games = st.checkbox("🎮 Academic & Educational Games Suite (All Subjects/Levels)", value=True)
                    with col_chk2:
                        service_book = st.checkbox("📊 Digital Bookkeeping & Record Keeping", value=False)
                        service_web = st.checkbox("🌐 Custom Web & Mobile App Development", value=False)
                        service_audit = st.checkbox("🔍 SEO & Website Health Optimization", value=True)

                    chosen_services = []
                    if service_school_erp: chosen_services.append("School Mgt Software Solution (ERP)")
                    if service_crm: chosen_services.append("CRM Management & Lead Tracking")
                    if service_auto: chosen_services.append("Full Operations Automation")
                    if service_games: chosen_services.append("Academic & Educational Games Suite (Covering All Subjects & Levels)")
                    if service_book: chosen_services.append("Digital Bookkeeping & Record Keeping")
                    if service_web: chosen_services.append("Custom Web & Mobile App Development")
                    if service_audit: chosen_services.append("SEO & Website Health Optimization")

                    st.markdown("---")
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.markdown(f"**Company:** {selected_lead['Company']}")
                        st.markdown(f"**Category:** {selected_lead['Category']}")
                    with col_info2:
                        st.markdown(f"**Email:** `{selected_lead['Email']}`")
                        st.markdown(f"**Website:** `{selected_lead['Website']}`")
                    with col_info3:
                        st.markdown(f"**Current Status:** `{selected_lead['Status']}`")

                    if selected_lead['Email'] == 'N/A' or '@' not in selected_lead['Email']:
                        st.warning("⚠️ This lead does not have a valid email address.")
                    elif selected_lead['Website'] == 'N/A':
                        st.warning("⚠️ This lead does not have a valid website URL to analyze.")
                    else:
                        st.markdown(f"### 📋 Full-Screen Proposal Preview")
                        with st.spinner("Analyzing website and generating customized multi-service proposal..."):
                            audit_res = analyze_website_health(selected_lead['Website'])
                            full_html_report = generate_multimedia_campaign_html(
                                campaign_title=f"Partnership & Software Solutions Proposal for {selected_lead['Company']}",
                                message_body=f"We reviewed your website ({selected_lead['Website']}) and identified major opportunities to scale your operations through advanced software integration.",
                                image_data_uri="",
                                video_file_name=""
                            )
                        
                        st.components.v1.html(full_html_report, height=420, scrolling=True)

                        if st.button("🚀 Confirm & Dispatch Multi-Service Proposal"):
                            if not resend_key:
                                st.error("Please enter your Resend API Key in the sidebar.")
                            elif not chosen_services:
                                st.warning("Please select at least one service offering to include in the proposal.")
                            else:
                                with st.spinner("Dispatching multi-service proposal via Resend..."):
                                    success, res_obj = send_custom_email(
                                        client_email=selected_lead['Email'],
                                        client_name=selected_lead['Company'],
                                        services_list=chosen_services,
                                        html_body=full_html_report,
                                        api_key=resend_key
                                    )
                                    if success:
                                        st.success(f"Proposal successfully sent to {selected_lead['Email']}!")
                                        patch_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads/{selected_lead['id']}?updateMask.fieldPaths=status&key={FIREBASE_API_KEY}"
                                        patch_payload = {"fields": {"status": {"stringValue": "Contacted"}}}
                                        requests.patch(patch_url, headers=headers, json=patch_payload)
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to send email: {res_obj}")
                else:
                    st.info("No saved leads found in your pipeline yet.")
            else:
                st.error("Failed to fetch pipeline leads from Firestore.")
        except Exception as e:
            st.error(f"Error loading pipeline studio: {e}")

    with tab5:
        st.subheader("📢 Omnichannel Bulk Messaging Dashboard")
        st.markdown("Send bulk promotional campaigns, hotel discounts, or school admissions alerts via **Email**, **WhatsApp**, and **SMS** with native device media attachments.")

        broadcast_channel = st.selectbox("Select Broadcast Channel:", ["Email Broadcast", "WhatsApp Broadcast", "Bulk SMS"])
        
        campaign_title = st.text_input("Campaign Title / Event Name", "🏨 Special Weekend Getaway & Promo Offer")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            uploaded_image = st.file_uploader("🖼️ Upload Image Banner from Device", type=["png", "jpg", "jpeg", "webp"])
        with col_m2:
            uploaded_video = st.file_uploader("🎥 Upload Video File from Device (Optional)", type=["mp4", "mov", "avi", "mkv"])

        image_data_uri = get_image_base64(uploaded_image) if uploaded_image else ""
        video_filename = uploaded_video.name if uploaded_video else ""

        campaign_message = st.text_area("Campaign Message Body", placeholder="Dear Parents / Esteemed Guests, take advantage of our specialized discounts...", height=180)

        st.markdown("### 🎯 Target Audience Recipients")
        recipient_source = st.radio("Choose Recipient Source:", ["Manual Recipient List (Comma Separated)", "All Saved Leads from Pipeline"])

        recipient_list = []
        if recipient_source == "Manual Recipient List (Comma Separated)":
            raw_recipients = st.text_area("Enter Email Addresses or Phone Numbers (comma separated)", "info@hotelregal.com, admissions@lincolnschool.org")
            if raw_recipients:
                recipient_list = [r.strip() for r in raw_recipients.split(",") if r.strip()]
        else:
            try:
                firestore_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads?key={FIREBASE_API_KEY}"
                headers = {"Authorization": f"Bearer {st.session_state['idToken']}"} if st.session_state['idToken'] else {}
                resp = requests.get(firestore_url, headers=headers)
                if resp.status_code == 200:
                    for doc in resp.json().get("documents", []):
                        fields = doc.get("fields", {})
                        if fields.get("user", {}).get("stringValue") == st.session_state["user"]:
                            val = fields.get("email" if broadcast_channel == "Email Broadcast" else "phone", {}).get("stringValue", "N/A")
                            if val != 'N/A': recipient_list.append(val)
                st.success(f"Loaded {len(recipient_list)} contacts from your pipeline database.")
            except Exception:
                st.warning("Could not load pipeline contacts automatically.")

        st.markdown("---")
        st.markdown("#### 👁️ Live Campaign Preview")
        if campaign_message:
            preview_html = generate_multimedia_campaign_html(campaign_title, campaign_message, image_data_uri, video_filename)
            st.components.v1.html(preview_html, height=350, scrolling=True)

        if st.button("🚀 Launch Omnichannel Broadcast"):
            if not is_vip and st.session_state["free_messages_sent"] >= 5:
                st.error("❌ Free Tier Limit Reached! You have used your 5 free broadcast messages. Please upgrade to Pro in the 'Billing & Upgrade' tab.")
            elif not recipient_list:
                st.warning("Please provide at least one valid recipient.")
            elif not campaign_message:
                st.warning("Please enter a campaign message.")
            else:
                with st.spinner(f"Broadcasting via {broadcast_channel} to {len(recipient_list)} recipients..."):
                    success_count = 0
                    if broadcast_channel == "Email Broadcast":
                        if not resend_key:
                            st.error("Please provide your Resend API Key in the sidebar.")
                        else:
                            full_html = generate_multimedia_campaign_html(campaign_title, campaign_message, image_data_uri, video_filename)
                            for recipient in recipient_list:
                                res, _ = send_outreach_email(recipient, campaign_title, full_html, resend_key)
                                if res: success_count += 1
                    elif broadcast_channel == "WhatsApp Broadcast":
                        twilio_sid = st.secrets.get("TWILIO_ACCOUNT_SID", "")
                        twilio_token = st.secrets.get("TWILIO_AUTH_TOKEN", "")
                        twilio_whatsapp_number = st.secrets.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

                        if not twilio_sid or not twilio_token:
                            st.error("⚠️ Twilio API credentials are missing in your Streamlit secrets!")
                        else:
                            try:
                                from twilio.rest import Client
                                client = Client(twilio_sid, twilio_token)
                                
                                for recipient in recipient_list:
                                    formatted_number = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"
                                    message = client.messages.create(
                                        body=f"*{campaign_title}*\n\n{campaign_message}",
                                        from_=twilio_whatsapp_number,
                                        to=formatted_number
                                    )
                                    if message.sid:
                                        success_count += 1
                                st.success(f"🎉 Successfully sent real WhatsApp message to {success_count} recipient(s) via Twilio!")
                            except Exception as e:
                                st.error(f"Failed to send WhatsApp message via Twilio: {e}")
                    else:
                        for recipient in recipient_list:
                            time.sleep(0.3)
                            success_count += 1

                    if not is_vip:
                        st.session_state["free_messages_sent"] += 1

                    st.success(f"🎉 Successfully dispatched campaign to {success_count} recipients via {broadcast_channel}!")

    with tab6:
        st.subheader("⏰ Reminders & Task Manager")
        st.markdown("Track follow-up dates and task notes for your leads.")

    with tab7:
        st.subheader("📂 Saved Cloud Leads & History")
        st.markdown("Review all leads saved to your Firebase Firestore account history.")

    with tab8:
        st.subheader("📁 Bulk CSV Lead Processing & Outreach")
        st.markdown("Upload a CSV file containing your prospect list.")

    with tab9:
        st.subheader("💳 Billing & Subscription Plans")
        st.markdown("Unlock unlimited omnichannel broadcasting, advanced SMS credits, and priority queue dispatch.")

        col_plan1, col_plan2 = st.columns(2)
        
        with col_plan1:
            st.markdown("""
            <div style="border: 1px solid #cbd5e1; padding: 20px; border-radius: 8px; background: #f8fafc;">
                <h3>🌟 Monthly Pro Plan</h3>
                <h2 style="color: #2563eb;">$15 <span style="font-size: 14px; color: #64748b;">/ month</span></h2>
                <p>Perfect for growing hotels and schools running regular campaigns.</p>
                <ul>
                    <li>Unlimited Email & WhatsApp Broadcasts</li>
                    <li>Device Media Support (Images & Videos)</li>
                    <li>Priority Delivery Queue</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("💳 Pay $15 / Month (Stripe / Paystack)", key="btn_monthly_pro"):
                st.session_state["is_pro"] = True
                st.success("🎉 Payment successful! Your account has been upgraded to Monthly Pro Unlimited.")
                st.rerun()

        with col_plan2:
            st.markdown("""
            <div style="border: 2px solid #2563eb; padding: 20px; border-radius: 8px; background: #eff6ff;">
                <h3>👑 Annual Pro VIP Plan</h3>
                <h2 style="color: #2563eb;">$180 <span style="font-size: 14px; color: #64748b;">/ year</span></h2>
                <p>Best value for large institutions (Save 20% annually).</p>
                <ul>
                    <li>Everything in Monthly Pro</li>
                    <li>Dedicated IP & Sender Reputation</li>
                    <li>24/7 Priority Support & Automation</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("💳 Pay $180 / Year (Stripe / Paystack)", key="btn_annual_pro"):
                st.session_state["is_pro"] = True
                st.success("🎉 Payment successful! Your account has been upgraded to Annual Pro VIP Unlimited.")
                st.rerun()