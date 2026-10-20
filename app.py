import streamlit as st
import os
import requests
import json
import time
import re
import pandas as pd
from generator import generate_outreach_email, generate_followup_email, send_outreach_email

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="JEdge Connect | AI B2B Lead Generator",
    page_icon="⚡",
    layout="wide"
)

# ==========================================
# 2. FIREBASE AUTH CONFIGURATION
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
    if not url or url == 'N/A':
        return "N/A"
    try:
        if not url.startswith("http"):
            url = "https://" + url
            
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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}"
    }
    firestore_payload = {
        "fields": {
            "user": {"stringValue": user_email},
            "title": {"stringValue": str(lead_data.get("title", "N/A"))},
            "category": {"stringValue": str(lead_data.get("categoryName", "N/A"))},
            "rating": {"doubleValue": float(lead_data.get("totalScore", 0.0))},
            "reviews": {"integerValue": int(lead_data.get("reviewsCount", 0))},
            "address": {"stringValue": str(lead_data.get("address", "N/A"))},
            "phone": {"stringValue": str(lead_data.get("phone", "N/A"))},
            "website": {"stringValue": str(lead_data.get("website", "N/A"))},
            "email": {"stringValue": str(lead_data.get("email", "N/A"))},
            "status": {"stringValue": "New Lead"},
            "timestamp": {"stringValue": time.strftime("%Y-%m-%d %H:%M:%S")}
        }
    }
    requests.post(url, headers=headers, data=json.dumps(firestore_payload))

# Initialize session state
if "user" not in st.session_state:
    st.session_state["user"] = None
if "idToken" not in st.session_state:
    st.session_state["idToken"] = None

# ==========================================
# 3. AUTHENTICATION GATE
# ==========================================
if not st.session_state["user"]:
    st.title("⚡ JEdge Connect: Secure Login")
    st.markdown("Please log in or create an account to access the B2B Lead Generator.")

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
    st.sidebar.success(f"Logged in as: **{st.session_state['user']}**")
    if st.sidebar.button("Log Out"):
        st.session_state["user"] = None
        st.session_state["idToken"] = None
        st.rerun()

    st.title("⚡ JEdge Connect: AI-Powered B2B Lead Generator & Outreach Assistant")
    st.markdown("Extract insights, find emails, manage your sales pipeline, and execute direct outreach.")

    st.sidebar.header("Configuration")
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    apify_token = st.sidebar.text_input("Apify API Token", type="password", value=os.environ.get("APIFY_TOKEN", ""))
    resend_key = st.sidebar.text_input("Resend API Key", type="password", value=os.environ.get("RESEND_API_KEY", ""))

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Manual Outreach", 
        "🌍 Live Google Maps Scraper", 
        "📊 Sales Pipeline Kanban", 
        "📂 Saved History & Export"
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
                                company_name=company_name,
                                industry=industry,
                                rating=rating,
                                reviews_count=reviews_count,
                                location=location,
                                api_key=openai_key
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
                            followup_draft = generate_followup_email(
                                company_name=company_name,
                                industry=industry,
                                api_key=openai_key
                            )
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
                            st.success(f"Email successfully sent! Message ID: {res.get('id')}")
                        else:
                            st.error(f"Failed to send email: {res.get('error')}")

    with tab2:
        st.subheader("Scrape Live Businesses & Find Emails")
        st.markdown("Pull real businesses, automatically hunt for contact emails, and save to cloud history.")
        
        search_query = st.text_input("Search Query (e.g., Hotels, Web Designers, Dental Clinics)", "Hotels", key="map_search_query")
        search_location = st.text_input("Search Location", "Abuja, Nigeria", key="map_search_location")
        max_leads = st.slider("Max Leads to Fetch", 1, 10, 3, key="map_max_leads")

        if st.button("Start Live Scraping & Email Hunt 🔍"):
            if not apify_token:
                st.error("Please provide your Apify API Token in the sidebar or secrets.")
            else:
                with st.spinner("Scraping live data & hunting for contact emails... (This may take a moment)"):
                    try:
                        run_url = f"https://api.apify.com/v2/acts/compass~crawler-google-places/runs?token={apify_token}"
                        payload = {
                            "searchStringsArray": [search_query],
                            "locationQuery": search_location,
                            "maxCrawledPlacesPerSearch": max_leads
                        }
                        res = requests.post(url=run_url, json=payload)
                        
                        if res.status_code in [200, 201]:
                            run_data = res.json()["data"]
                            dataset_id = run_data["defaultDatasetId"]
                            run_id = run_data["id"]
                            
                            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"
                            for _ in range(30):
                                status_res = requests.get(status_url)
                                if status_res.status_code == 200:
                                    status = status_res.json()["data"]["status"]
                                    if status == "SUCCEEDED":
                                        break
                                    elif status in ["FAILED", "ABORTED"]:
                                        st.error(f"Apify actor run failed with status: {status}")
                                        break
                                time.sleep(2)
                            
                            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}"
                            data_res = requests.get(dataset_url)
                            
                            if data_res.status_code == 200:
                                items = data_res.json()
                                if items:
                                    st.success(f"Successfully scraped {len(items)} leads and found contact emails!")
                                    
                                    clean_leads = []
                                    for item in items:
                                        website = item.get('website', 'N/A')
                                        found_email = extract_emails_from_website(website)
                                        
                                        lead_dict = {
                                            "title": item.get('title', 'N/A'),
                                            "categoryName": item.get('categoryName', 'N/A'),
                                            "totalScore": item.get('totalScore', 0.0),
                                            "reviewsCount": item.get('reviewsCount', 0),
                                            "address": item.get('address', 'N/A'),
                                            "phone": item.get('phone', 'N/A'),
                                            "website": website,
                                            "email": found_email
                                        }
                                        clean_leads.append(lead_dict)
                                        save_lead_to_firestore(st.session_state["user"], lead_dict, st.session_state["idToken"])
                                    
                                    df = pd.DataFrame(clean_leads)
                                    st.dataframe(df)
                                    
                                    csv_data = df.to_csv(index=False).encode('utf-8')
                                    st.download_button(
                                        label="📥 Download Scraped Leads & Emails as CSV",
                                        data=csv_data,
                                        file_name="jedge_connect_leads.csv",
                                        mime="text/csv"
                                    )
                                    
                                    for idx, item in enumerate(clean_leads, 1):
                                        st.markdown(f"### {idx}. {item['title']}")
                                        st.write(f"**Category:** {item['categoryName']} | **Rating:** {item['totalScore']} ⭐ ({item['reviewsCount']} reviews)")
                                        st.write(f"**Address:** {item['address']}")
                                        
                                        email = item['email']
                                        if email != 'N/A':
                                            st.markdown(f"**Email:** [{email}](mailto:{email})")
                                        else:
                                            st.write("**Email:** N/A")
                                            
                                        phone = item['phone']
                                        if phone != 'N/A':
                                            clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
                                            st.markdown(f"**Phone:** [{phone}](tel:{clean_phone}) | 💬 [Chat on WhatsApp](https://wa.me/{clean_phone.replace('+', '')})")
                                        else:
                                            st.write("**Phone:** N/A")
                                            
                                        website = item['website']
                                        if website != 'N/A':
                                            st.markdown(f"**Website:** [{website}]({website})")
                                        else:
                                            st.write("**Website:** N/A")
                                            
                                        st.markdown("---")
                                else:
                                    st.warning("No leads found for this query/location.")
                            else:
                                st.error("Failed to fetch dataset items from Apify.")
                        else:
                            error_detail = res.json().get("error", {}).get("message", res.text)
                            st.error(f"Apify API returned error: {error_detail}")
                    except Exception as e:
                        st.error(f"Scraping failed: {e}")

    with tab3:
        st.subheader("📊 Sales Pipeline Kanban Board")
        st.markdown("Track your prospecting progress across different pipeline stages.")
        
        if st.button("🔄 Refresh Kanban Board"):
            st.rerun()

        try:
            firestore_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads?key={FIREBASE_API_KEY}"
            headers = {"Authorization": f"Bearer {st.session_state['idToken']}"} if st.session_state['idToken'] else {}
            response = requests.get(firestore_url, headers=headers)
            
            if response.status_code == 200:
                documents = response.json().get("documents", [])
                user_leads = []
                
                for doc in documents:
                    fields = doc.get("fields", {})
                    if fields.get("user", {}).get("stringValue") == st.session_state["user"]:
                        doc_path = doc.get("name", "") # Full resource name for updating
                        user_leads.append({
                            "id": doc_path.split("/")[-1],
                            "Company": fields.get("title", {}).get("stringValue", "N/A"),
                            "Category": fields.get("category", {}).get("stringValue", "N/A"),
                            "Phone": fields.get("phone", {}).get("stringValue", "N/A"),
                            "Email": fields.get("email", {}).get("stringValue", "N/A"),
                            "Status": fields.get("status", {}).get("stringValue", "New Lead")
                        })
                
                if user_leads:
                    stages = ["New Lead", "Contacted", "Meeting Booked", "Converted"]
                    cols = st.columns(len(stages))
                    
                    for idx, stage in enumerate(stages):
                        with cols[idx]:
                            st.markdown(f"### {stage}")
                            stage_leads = [l for l in user_leads if l["Status"] == stage]
                            st.caption(f"{len(stage_leads)} leads")
                            
                            for lead in stage_leads:
                                with st.container(border=True):
                                    st.markdown(f"**{lead['Company']}**")
                                    st.text(f"📞 {lead['Phone']}")
                                    st.text(f"✉️ {lead['Email']}")
                                    
                                    # Quick status switcher
                                    new_status = st.selectbox(
                                                "Move to:", 
                                                stages, 
                                                index=stages.index(stage), 
                                                key=f"status_{lead['id']}"
                                    )
                                    
                                    if new_status != stage:
                                        # Update status in Firestore via REST PATCH
                                        patch_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads/{lead['id']}?updateMask.fieldPaths=status&key={FIREBASE_API_KEY}"
                                        patch_payload = {
                                            "fields": {
                                                "status": {"stringValue": new_status}
                                            }
                                        }
                                        patch_res = requests.patch(patch_url, headers=headers, json=patch_payload)
                                        if patch_res.status_code == 200:
                                            st.success(f"Moved to {new_status}!")
                                            time.sleep(0.5)
                                            st.rerun()
                                        else:
                                            st.error("Failed to update status.")
                else:
                    st.info("No saved leads found in your pipeline yet. Scrape some leads first!")
            else:
                st.error("Failed to fetch pipeline from Firestore.")
        except Exception as e:
            st.error(f"Error loading Kanban board: {e}")

    with tab4:
        st.subheader("📂 Saved Cloud Leads & History")
        st.markdown("Review all leads saved to your Firebase Firestore account history and export them.")
        
        if st.button("🔄 Refresh History"):
            try:
                firestore_url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads?key={FIREBASE_API_KEY}"
                headers = {"Authorization": f"Bearer {st.session_state['idToken']}"} if st.session_state['idToken'] else {}
                response = requests.get(firestore_url, headers=headers)
                
                if response.status_code == 200:
                    documents = response.json().get("documents", [])
                    user_leads = []
                    
                    for doc in documents:
                        fields = doc.get("fields", {})
                        if fields.get("user", {}).get("stringValue") == st.session_state["user"]:
                            user_leads.append({
                                "Company": fields.get("title", {}).get("stringValue", "N/A"),
                                "Category": fields.get("category", {}).get("stringValue", "N/A"),
                                "Rating": fields.get("rating", {}).get("doubleValue", 0.0),
                                "Reviews": fields.get("reviews", {}).get("integerValue", 0),
                                "Address": fields.get("address", {}).get("stringValue", "N/A"),
                                "Phone": fields.get("phone", {}).get("stringValue", "N/A"),
                                "Website": fields.get("website", {}).get("stringValue", "N/A"),
                                "Email": fields.get("email", {}).get("stringValue", "N/A"),
                                "Status": fields.get("status", {}).get("stringValue", "New Lead"),
                                "Saved At": fields.get("timestamp", {}).get("stringValue", "N/A")
                            })
                    
                    if user_leads:
                        history_df = pd.DataFrame(user_leads)
                        st.dataframe(history_df)
                        
                        history_csv = history_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download History CSV",
                            data=history_csv,
                            file_name="jedge_connect_history.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No saved leads found in your cloud history yet.")
                else:
                    st.error("Failed to fetch history from Firestore.")
            except Exception as e:
                st.error(f"Error loading history: {e}")