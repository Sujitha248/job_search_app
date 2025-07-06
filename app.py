import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Set up page
st.set_page_config(page_title="Naukri Job Search", layout="wide")

# Load dataset
@st.cache_data
def load_data():
    df = pd.read_csv("naukri_com-job_sample.csv")
    df['city'] = df['joblocation_address'].astype(str).str.split(',').str[0]
    return df.drop_duplicates()

df = load_data()

# Sidebar filters
st.sidebar.title("🔍 Filter Jobs")
search_city = st.sidebar.text_input("Enter City Name")
search_company = st.sidebar.text_input("Enter Company Name")
search_title = st.sidebar.text_input("Enter Job Title")

# Filter logic
filtered_df = df.copy()

if search_city:
    filtered_df = filtered_df[filtered_df['city'].str.contains(search_city, case=False, na=False)]

if search_company:
    filtered_df = filtered_df[filtered_df['company'].str.contains(search_company, case=False, na=False)]

if search_title:
    filtered_df = filtered_df[filtered_df['jobtitle'].str.contains(search_title, case=False, na=False)]

# Main Output
st.title("📊 Naukri Job Data Explorer")
st.write(f"### Showing {len(filtered_df)} results")

# Show filtered table
st.dataframe(filtered_df[['jobtitle', 'company', 'city', 'experience', 'industry']].reset_index(drop=True))

# Show some charts
st.write("### 🔝 Top Job Titles")
top_titles = filtered_df['jobtitle'].value_counts().head(10)
fig, ax = plt.subplots()
sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax)
st.pyplot(fig)

st.write("### 🏙️ Top Cities")
top_cities = filtered_df['city'].value_counts().head(10)
fig, ax = plt.subplots()
sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax)
st.pyplot(fig)


from prophet import Prophet
import matplotlib.pyplot as plt

st.subheader("🔮 Skill Demand Forecast ")

# ✅ Extract all skills from 'Key Skills' column
if 'skills' in df.columns:
    skill_series = df['skills'].dropna().str.lower().str.split(', ')
    flat_skills = [skill.strip() for sublist in skill_series for skill in sublist]
    unique_skills = sorted(set(flat_skills))

    # ✅ Skill dropdown
    selected_skill = st.selectbox("Select a skill to forecast:", unique_skills)

    # ✅ Prepare time series for selected skill
    skill_df = df[df['skills'].str.contains(selected_skill, case=False, na=False)].copy()
    skill_df['postdate'] = pd.to_datetime(skill_df['postdate'], errors='coerce')
    skill_df.dropna(subset=['postdate'], inplace=True)

    if not skill_df.empty:
        skill_df['Month'] = skill_df['postdate'].dt.to_period('M').astype(str)
        monthly_trend = skill_df.groupby('Month').size().reset_index(name='Count')
        monthly_trend.rename(columns={'Month': 'ds', 'Count': 'y'}, inplace=True)
        monthly_trend['ds'] = pd.to_datetime(monthly_trend['ds'])

        # ✅ Forecast using Prophet
        model = Prophet()
        model.fit(monthly_trend)
        future = model.make_future_dataframe(periods=6, freq='M')
        forecast = model.predict(future)

        # ✅ Plot forecast
        st.markdown(f"📈 Forecasting demand for *{selected_skill}*")
        fig = model.plot(forecast)
        st.pyplot(fig)
    else:
        st.warning(f"No postings found for skill: {selected_skill}")
else:
    st.error("❌ 'skills' column not found in dataset.")