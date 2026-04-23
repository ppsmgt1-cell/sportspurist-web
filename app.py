import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# ⚙️ APP CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="SportsPurist Fox Valley", 
    page_icon="🏆", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 🗄️ DATA CONNECTIONS (READ ONLY & FAST)
# ==========================================
@st.cache_data(ttl=300) 
def get_live_schedules():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open("PureSport_Database").sheet1
        data = sheet.get_all_records()
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df[df["status"] != "Ignored"]
            df["match_date"] = pd.to_datetime(df["match_date"], errors='coerce')
            df = df.dropna(subset=['match_date'])
            df = df.sort_values(by="match_date", ascending=True)
        return df
    except Exception as e:
        return pd.DataFrame()

def save_to_subscribers(email, location, sport):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(st.secrets["gcp_service_account"]), scope)
        client = gspread.authorize(creds)
        sheet = client.open("PureSport_Database").worksheet("Subscribers")
        
        # Format date to match your existing YYYY-MM-DD format
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Matches your columns: email, location, all(sport), date_joined, source
        sheet.append_row([email, location, sport, today_str, "Beta Draft Party"])
        return True
    except Exception as e:
        return False

df = get_live_schedules()

# ==========================================
# 🎨 MOBILE-FIRST UI
# ==========================================
st.markdown("<h1 style='text-align: center; color: #1a5c28;'>SportsPurist</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>The master directory for Fox Valley adult sports.</h4>", unsafe_allow_html=True)
st.markdown("---")

if not df.empty:
    today = pd.Timestamp(datetime.now().date())
    fourteen_days = today + timedelta(days=14)
    
    st.subheader("🔥 Starting Soon")
    st.caption("Leagues kicking off in the next 14 days.")
    
    spotlight_df = df[(df['match_date'] >= today) & (df['match_date'] <= fourteen_days)].head(3)
    
    if spotlight_df.empty:
        st.info("No leagues starting in the next 14 days. Check the full directory below!")
    else:
        for _, row in spotlight_df.iterrows():
            with st.container(border=True):
                st.markdown(f"### 🎯 {row['match_title']}")
                st.write(f"**Sport:** {row['sport']} | **City:** {row['city']}")
                st.write(f"**Start Date:** {row['match_date'].strftime('%b %d, %Y')}")
                st.write(f"**Location:** {row['venue_name']}")
    
    st.markdown("---")

    st.subheader("🔎 Find a League")
    
    sports_list = ["All Sports"] + sorted(df['sport'].unique().tolist())
    cities_list = ["All Cities"] + sorted(df['city'].unique().tolist())
    
    col1, col2 = st.columns(2)
    with col1:
        sel_sport = st.selectbox("Sport", sports_list)
    with col2:
        sel_city = st.selectbox("City", cities_list)
        
    filtered_df = df.copy()
    filtered_df = filtered_df[filtered_df['match_date'] >= today] 
    
    if sel_sport != "All Sports":
        filtered_df = filtered_df[filtered_df['sport'] == sel_sport]
    if sel_city != "All Cities":
        filtered_df = filtered_df[filtered_df['city'] == sel_city]

    st.markdown("<br>", unsafe_allow_html=True)
    
    if filtered_df.empty:
        st.warning(f"No upcoming {sel_sport} leagues found in {sel_city}.")
    else:
        for _, row in filtered_df.head(10).iterrows():
            with st.container(border=True):
                st.markdown(f"#### {row['match_title']}")
                st.write(f"📅 **{row['match_date'].strftime('%b %d, %Y')}**")
                st.caption(f"📍 {row['venue_name']}, {row['city']}")

else:
    st.info("The database is currently updating. Check back soon!")

st.markdown("---")

# --- 5. THE TRAP (WAITLIST FORM) ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("Need a team?")
st.write("Join the Locker Room waitlist. We'll let you know when local teams are looking for free agents.")

with st.container(border=True):
    with st.form("waitlist_form", clear_on_submit=True):
        w_email = st.text_input("Email Address")
        w_location = st.text_input("Your City (e.g., Appleton)")
        w_sport = st.text_input("Primary Sport (e.g., Softball, Darts)")
        
        submit_btn = st.form_submit_button("Join Waitlist", type="primary", use_container_width=True)
        
        if submit_btn:
            if w_email and w_location and w_sport:
                success = save_to_subscribers(w_email, w_location, w_sport)
                if success:
                    st.success("You're on the list! We'll be in touch.")
                    st.balloons()
                else:
                    st.error("Something went wrong. Try again later.")
            else:
                st.error("Please fill out all fields.")
