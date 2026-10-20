import streamlit as st
import os
import requests
import json
import time
import pandas as pd
from generator import generate_outreach_email

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

def save_lead_to_firestore(user_email, lead_data, id_token):
    """Saves a scraped lead to Firebase Firestore using REST API"""
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/leads?key={FIREBASE_API_KEY}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {id_token}"
    }
    
    # Format data for Firestore REST API structure
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
    st.markdown("Extract firmographic insights, filter by your ICP, generate custom emails, and export your pipeline.")

    # Sidebar API Configurations
    st.sidebar.header("Configuration")
    openai_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.environ.get("OPENAI_API_KEY", ""))
    apify_token = st.sidebar.text_input("Apify API Token", type="password", value=os.environ.get("APIFY_TOKEN", ""))

    # App Navigation Tabs
    tab1, tab2, tab3 = st.tabs(["📝 Manual Lead Entry", "🌍 Live Google Maps Scraper", "📂 Saved Leads History"])

    with tab1:
        st.subheader("Add Target Lead Details Manually")
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", "Lagos Premier Logistics")
            industry = st.text_input("Category / Industry", "Courier & Delivery")
        with col2:
            rating = st.number_input("Google Rating", 1.0, 5.0, 4.7)
            reviews_count = st.number_input("Reviews Count", 0, 5000, 85)
        
        location = st.text_input("Location", "Lagos, Nigeria")

        if st.button("Generate Personalized Outreach"):
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
                        st.subheader("Generated Cold Email Preview")
                        st.code(email_draft, language="markdown")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

    with tab2:
        st.subheader("Scrape Live Businesses from Google Maps")
        st.markdown("Pull real businesses, export to CSV, and save them to your secure cloud account.")
        
        search_query = st.text_input("Search Query (e.g., Hotels, Web Designers, Dental Clinics)", "Hotels", key="map_search_query")
        search_location = st.text_input("Search Location", "Abuja, Nigeria", key="map_search_location")
        max_leads = st.slider("Max Leads to Fetch", 1, 10, 3, key="map_max_leads")

        if st.button("Start Live Scraping 🔍"):
            if not apify_token:
                st.error("Please provide your Apify API Token in the sidebar or secrets.")
            else:
                with st.spinner("Scraping live data from Google Maps... (This may take a moment)"):
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
                                    st.success(f"Successfully scraped {len(items)} live leads!")
                                    
                                    # Process and save each lead to Firestore
                                    clean_leads = []
                                    for item in items:
                                        lead_dict = {
                                            "title": item.get('title', 'N/A'),
                                            "categoryName": item.get('categoryName', 'N/A'),
                                            "totalScore": item.get('totalScore', 0.0),
                                            "reviewsCount": item.get('reviewsCount', 0),
                                            "address": item.get('address', 'N/A'),
                                            "phone": item.get('phone', 'N/A'),
                                            "website": item.get('website', 'N/A')
                                        }
                                        clean_leads.append(lead_dict)
                                        save_lead_to_firestore(st.session_state["user"], lead_dict, st.session_state["idToken"])
                                    
                                    # Convert to Pandas DataFrame for display & CSV export
                                    df = pd.DataFrame(clean_leads)
                                    st.dataframe(df)
                                    
                                    # CSV Export Button
                                    csv_data = df.to_csv(index=False).encode('utf-8')
                                    st.download_button(
                                        label="📥 Download Scraped Leads as CSV",
                                        data=csv_data,
                                        file_name="jedge_connect_leads.csv",
                                        mime="text/csv"
                                    )
                                    
                                    # Detailed View
                                    for idx, item in enumerate(items, 1):
                                        st.markdown(f"### {idx}. {item.get('title', 'N/A')}")
                                        st.write(f"**Category:** {item.get('categoryName', 'N/A')} | **Rating:** {item.get('totalScore', 'N/A')} ⭐ ({item.get('reviewsCount', 0)} reviews)")
                                        st.write(f"**Address:** {item.get('address', 'N/A')}")
                                        st.write(f"**Phone:** {item.get('phone', 'N/A')} | **Website:** {item.get('website', 'N/A')}")
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
        st.subheader("Your Saved Cloud Leads")
        st.markdown("Review all leads saved to your Firebase Firestore account history.")
        
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
                        # Filter by currently logged in user
                        if fields.get("user", {}).get("stringValue") == st.session_state["user"]:
                            user_leads.append({
                                "Company": fields.get("title", {}).get("stringValue", "N/A"),
                                "Category": fields.get("category", {}).get("stringValue", "N/A"),
                                "Rating": fields.get("rating", {}).get("doubleValue", 0.0),
                                "Reviews": fields.get("reviews", {}).get("integerValue", 0),
                                "Address": fields.get("address", {}).get("stringValue", "N/A"),
                                "Phone": fields.get("phone", {}).get("stringValue", "N/A"),
                                "Website": fields.get("website", {}).get("stringValue", "N/A"),
                                "Saved At": fields.get("timestamp", {}).get("stringValue", "N/A")
                            })
                    
                    if user_leads:
                        history_df = pd.DataFrame(user_leads)
                        st.dataframe(history_df)
                        
                        # Export History to CSV
                        history_csv = history_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download History CSV",
                            data=history_csv,
                            file_name="jedge_connect_history.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No saved leads found in your cloud history yet. Try scraping some leads!")
                else:
                    st.error("Failed to fetch history from Firestore.")
            except Exception as e:
                st.error(f"Error loading history: {e}")