import streamlit as st
import requests 
import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt 
import os

#Page configuration

st.set_page_config(page_title="Real-Time Job Explorer", layout="wide") 
st.title("Real-Time Job Explorer")

#Input fields

st.sidebar.header("Search Filters") 
job_query = st.sidebar.text_input("Enter Job Title", "") 
location_query = st.sidebar.text_input("Enter Location", "India")

#Optional: Add fallback filename
FALLBACK_FILE = "fallback_jobs.csv"

def fetch_jobs_from_api(query, location): 
    url = "https://jsearch.p.rapidapi.com/search" 
    querystring = {"query": f"{query} in {location}", "num_pages": "3"}

headers = {
    "X-RapidAPI-Key": "dea4bfe97bmsh4ea7b4ffb63140bp1b454cjsn69c6d76829c3",
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
if response.status_code == 200:
    data = response.json()
    jobs = data.get("data", [])
    return jobs
else:
    raise ValueError(f"API Error: {response.status_code}")

def load_fallback(): 
    if os.path.exists(FALLBACK_FILE): 
        return pd.read_csv(FALLBACK_FILE) 
    else: 
        st.warning("⚠ API failed and no fallback data is available.") 
        return pd.DataFrame()

def save_fallback(df): 
    df.to_csv(FALLBACK_FILE, index=False)

#Fetch or load data

try: 
    jobs_data = fetch_jobs_from_api(job_query, location_query) 
    if jobs_data: 
        df = pd.DataFrame(jobs_data) 
        save_fallback(df) 
    else: 
        df = load_fallback() 
except: 
    df = load_fallback()

#If data exists, show output

if not df.empty: 
    # Clean and select 
    columns_to_keep = [ 'employer_name', 'job_title', 'job_city', 'job_country', 'job_posted_at_datetime_utc', 'job_apply_link', 'job_required_skills' ] 
    df = df[[col for col in columns_to_keep if col in df.columns]]

# Format date
if 'job_posted_at_datetime_utc' in df.columns:
    df['job_posted_at_datetime_utc'] = pd.to_datetime(df['job_posted_at_datetime_utc']).dt.date

st.subheader(f"Showing {len(df)} jobs for '{job_query}' in '{location_query}'")
st.dataframe(df, use_container_width=True)

# --- Skills Analysis ---
if 'job_required_skills' in df.columns and df['job_required_skills'].notna().any():
    skills_series = df['job_required_skills'].dropna().str.split(', ').explode()
    top_skills = skills_series.value_counts().head(10)

    st.subheader("Top Required Skills")
    fig, ax = plt.subplots()
    sns.barplot(x=top_skills.values, y=top_skills.index, palette="coolwarm", ax=ax)
    ax.set_xlabel("Demand Count")
    ax.set_ylabel("Skill")
    st.pyplot(fig)

else: 
    st.error("No job data available to display.")