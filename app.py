import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(page_title="Real-Time Job Explorer", layout="wide")
st.title("🔍 Real-Time Job Explorer")

# Sidebar Inputs
job_query = st.sidebar.text_input("Enter Job Title", "")
location_query = st.sidebar.text_input("Enter Location", "India")
selected_skill = st.sidebar.text_input("Filter by Skill (optional)")

# Fallback CSV
FALLBACK_FILE = "fallback_jobs.csv"

# Function to fetch jobs from API
def fetch_jobs(query, location):
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {"query": f"{query} in {location}", "num_pages": "3"}

    headers = {
        "X-RapidAPI-Key": "dea4bfe97bmsh4ea7b4ffb63140bp1b454cjsn69c6d76829c3",  # Replace with your API key
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        raise ValueError("API error")

# Function to load fallback
def load_fallback():
    if os.path.exists(FALLBACK_FILE):
        return pd.read_csv(FALLBACK_FILE)
    else:
        st.warning("⚠ No fallback data found.")
        return pd.DataFrame()

# Function to save fallback
def save_fallback(df):
    df.to_csv(FALLBACK_FILE, index=False)

# Try to load from API, else fallback
try:
    jobs = fetch_jobs(job_query, location_query)
    df = pd.DataFrame(jobs)
    if not df.empty:
        save_fallback(df)
except:
    st.warning("⚠ Using fallback data (API failed).")
    df = load_fallback()

# Display and filter results
if not df.empty:
    if 'job_posted_at_datetime_utc' in df.columns:
        df['job_posted_at_datetime_utc'] = pd.to_datetime(df['job_posted_at_datetime_utc']).dt.date

    if 'job_required_skills' in df.columns:
        df['job_required_skills'] = df['job_required_skills'].fillna("N/A")

    if selected_skill:
        df = df[df['job_required_skills'].str.contains(selected_skill, case=False, na=False)]

    st.subheader(f"Found {len(df)} jobs for '{job_query}' in '{location_query}'")
    st.dataframe(df[['employer_name', 'job_title', 'job_city', 'job_country', 'job_posted_at_datetime_utc', 'job_required_skills', 'job_apply_link']], use_container_width=True)

    # Job count by city
    if 'job_city' in df.columns:
        city_count = df['job_city'].value_counts().head(10)
        st.subheader("📍 Top Cities by Job Count")
        fig1, ax1 = plt.subplots()
        sns.barplot(x=city_count.values, y=city_count.index, palette="viridis", ax=ax1)
        ax1.set_xlabel("Number of Jobs")
        ax1.set_ylabel("City")
        st.pyplot(fig1)

    # Top required skills
    if 'job_required_skills' in df.columns:
        skill_series = df['job_required_skills'].str.split(', ').explode().value_counts().head(10)
        st.subheader("💼 Top In-Demand Skills")
        fig2, ax2 = plt.subplots()
        sns.barplot(x=skill_series.values, y=skill_series.index, palette="coolwarm", ax=ax2)
        ax2.set_xlabel("Frequency")
        ax2.set_ylabel("Skill")
        st.pyplot(fig2)

    # Job count by date
    if 'job_posted_at_datetime_utc' in df.columns:
        date_count = df['job_posted_at_datetime_utc'].value_counts().sort_index()
        st.subheader("📆 Job Postings Over Time")
        fig3, ax3 = plt.subplots()
        date_count.plot(kind='bar', ax=ax3)
        ax3.set_xlabel("Date")
        ax3.set_ylabel("Number of Postings")
        st.pyplot(fig3)
else:
    st.error("No job data available.")