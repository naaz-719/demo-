import streamlit as st
import pandas as pd
import requests
import joblib
import os
import altair as alt
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(
    page_title="Voyage Analytics Pro",
    page_icon="✈️",
    layout="wide"
)

BACKEND_URL = "https://voyage-analytics-r34b.onrender.com"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= DARK GLASS CSS =================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}
.glass-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.metric-box {
    background: rgba(0,0,0,0.4);
    padding: 25px;
    border-radius: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "history" not in st.session_state:
    st.session_state.history = []

if "flight_price" not in st.session_state:
    st.session_state.flight_price = 0

if "destination" not in st.session_state:
    st.session_state.destination = None

# ================= LOGIN =================
def login_page():
    st.title("🔐 Voyage Analytics Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user and pwd:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ================= LOAD FEATURE NAMES =================
@st.cache_resource
def load_features():
    return joblib.load(os.path.join(BASE_DIR, "feature_names.pkl"))

feature_names = load_features()

# ================= EXTRACT OPTIONS =================
from_options = sorted([c.replace("from_", "") for c in feature_names if c.startswith("from_")])
to_options = sorted([c.replace("to_", "") for c in feature_names if c.startswith("to_")])
agency_options = sorted([c.replace("agency_", "") for c in feature_names if c.startswith("agency_")])
flight_type_options = sorted([c.replace("flightType_", "") for c in feature_names if c.startswith("flightType_")])

# ================= DISTANCE AUTO-MAP =================
DISTANCE_MAP = {
    ("Recife (PE)", "Brasilia (DF)"): 1650,
    ("Recife (PE)", "Sao Paulo (SP)"): 2120,
    ("Recife (PE)", "Rio de Janeiro (RJ)"): 2330,
    ("Natal (RN)", "Sao Paulo (SP)"): 2940,
    ("Florianopolis (SC)", "Sao Paulo (SP)"): 705,
}

def get_distance(frm, to):
    return DISTANCE_MAP.get((frm, to)) or DISTANCE_MAP.get((to, frm)) or 1000

# ================= HEADER =================
st.title("✈️ Voyage Analytics Pro")
st.caption(f"Welcome, {st.session_state.username}")

tab1, tab2 = st.tabs(["✈️ Flight Planning", "🏨 Hotel Planning"])

# =====================================================
# ================= FLIGHT TAB ========================
# =====================================================
with tab1:

    if "from_city" not in st.session_state:
        st.session_state.from_city = from_options[0]

    if "to_city" not in st.session_state:
        st.session_state.to_city = to_options[1]

    col1, col2, col3 = st.columns([4,1,4])

    with col1:
        st.session_state.from_city = st.selectbox(
            "From",
            from_options,
            index=from_options.index(st.session_state.from_city)
        )

    with col2:
        if st.button("🔄"):
            st.session_state.from_city, st.session_state.to_city = (
                st.session_state.to_city,
                st.session_state.from_city
            )
            st.rerun()

    with col3:
        filtered_to = [c for c in to_options if c != st.session_state.from_city]

        if st.session_state.to_city not in filtered_to:
            st.session_state.to_city = filtered_to[0]

        st.session_state.to_city = st.selectbox(
            "To",
            filtered_to,
            index=filtered_to.index(st.session_state.to_city)
        )

    travel_date = st.date_input("Travel Date", datetime.today())

    day = travel_date.day
    month = travel_date.month
    year = travel_date.year

    agency = st.selectbox("Agency", agency_options)
    flight_type = st.selectbox("Flight Type", flight_type_options)

    distance = get_distance(st.session_state.from_city, st.session_state.to_city)

    if st.button("💰 Predict Flight Price"):

        payload = {
            "from": st.session_state.from_city,
            "to": st.session_state.to_city,
            "agency": agency,
            "flightType": flight_type,
            "distance": distance,
            "day": day,
            "month": month,
            "year": year
        }

        res = requests.post(f"{BACKEND_URL}/predict-flight", json=payload)

        if res.status_code == 200:
            price = res.json()["predicted_price"]

            st.session_state.flight_price = price
            st.session_state.destination = st.session_state.to_city

            st.markdown(f"""
            <div class="metric-box">
                <h2>Estimated Flight Price</h2>
                <h1>₹ {price}</h1>
            </div>
            """, unsafe_allow_html=True)

            st.session_state.history.append({
                "from": st.session_state.from_city,
                "to": st.session_state.to_city,
                "price": price
            })

        else:
            st.error(res.json())

# =====================================================
# ================= HOTEL TAB =========================
# =====================================================
with tab2:

    if st.session_state.destination:
        place = st.session_state.destination
        st.info(f"Hotel city auto-selected: {place}")
    else:
        place = st.text_input("Destination City")

    days = st.number_input("Stay Duration", 1, 30, 2)
    max_total = st.number_input("Total Budget", 1000, 200000, 20000)

    if st.button("🏨 Find Hotels"):

        payload = {
            "place": place,
            "days": days,
            "max_total": max_total
        }

        res = requests.post(f"{BACKEND_URL}/recommend-hotels", json=payload)

        if res.status_code == 200:

            hotels = res.json()["recommended_hotels"]

            for hotel in hotels:

                flight_price = st.session_state.flight_price
                total_trip = hotel["calculated_total"] + flight_price

                status = "✅ Within Budget" if total_trip <= max_total else "❌ Over Budget"

                st.markdown(f"""
                <div class="glass-card">
                    <h3>{hotel['name']}</h3>
                    <p>Price per Night: ₹ {hotel['price']}</p>
                    <p>Stay Cost: ₹ {hotel['calculated_total']}</p>
                    <p><b>Total Trip Cost: ₹ {total_trip}</b></p>
                    <p>{status}</p>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.error(res.json())

# =====================================================
# ================= SIDEBAR ===========================
# =====================================================
st.sidebar.title("📜 Booking History")

if st.session_state.history:
    for h in reversed(st.session_state.history):
        st.sidebar.write(f"{h['from']} ➜ {h['to']} | ₹ {h['price']}")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()
