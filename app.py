import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from prophet import Prophet

# ------------------ Streamlit Setup ------------------
st.set_page_config(page_title="Job Explorer", layout="wide")
st.title("💼 Real-Time Job Search with Skills & Trends")

# ------------------ Session State Init ------------------
if "job_data" not in st.session_state:
    st.session_state["job_data"] = None

# ------------------ User Input Section ------------------
st.markdown("## 🔍 Enter Search Criteria")
job_title = st.text_input("Job Title:", "")
location = st.text_input("Location:", "India")

st.markdown("### 🎯 Optional Filters")
skill = st.text_input("Required Skill (optional):", "")
experience = st.selectbox("Experience Level:", ["", "Internship", "Entry level", "Mid-Senior level", "Director"])
industry = st.text_input("Industry (optional):", "")

# ------------------ Search Button ------------------
if st.button("🔍 Search Jobs"):
    with st.spinner("Fetching jobs..."):
        query = f"{job_title} in {location}"
        if skill:
            query += f" {skill}"
        if experience:
            query += f" {experience}"
        if industry:
            query += f" {industry}"

        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": "dea4bfe97bmsh4ea7b4ffb63140bp1b454cjsn69c6d76829c3",  # 🔑 Replace with your actual API Key
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        params = {
            "query": query,
            "page": "1",
            "num_pages": "3"
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            jobs = response.json().get("data", [])

            if jobs:
                known_skills = [
                    "Python", "SQL", "Excel", "Power BI", "Machine Learning",
                    "Deep Learning", "NLP", "Communication", "Java", "C++",
                    "AWS", "Azure", "Git", "Tableau", "Teamwork"
                ]

                job_list = []
                for job in jobs:
                    desc = job.get("job_description", "").lower()
                    found_skills = [s for s in known_skills if s.lower() in desc]
                    job_list.append({
                        "Job Title": job.get("job_title"),
                        "Company": job.get("employer_name"),
                        "Location": job.get("job_city") if job.get("job_city") else "Not Specified",
                        "Posted": job.get("job_posted_at_datetime_utc"),
                        "Skills": ", ".join(found_skills) if found_skills else "N/A",
                        "Apply Link": job.get("job_apply_link")
                    })

                df = pd.DataFrame(job_list)
                df["Posted"] = pd.to_datetime(df["Posted"]).dt.date
                df['Apply Link'] = df['Apply Link'].apply(lambda x: f"[Apply]({x})")
                st.session_state["job_data"] = df.copy()
            else:
                st.warning("😕 No jobs found.")
        else:
            st.error(f"❌ API Error: {response.status_code}")

# ------------------ Show Filters and Charts ------------------
if st.session_state["job_data"] is not None:
    df = st.session_state["job_data"]

    st.markdown("## 🎛 Filter Results")

    # Filters
    available_cities = df["Location"].dropna().unique().tolist()
    if "Not Specified" in available_cities:
        available_cities.remove("Not Specified")
    selected_city = st.selectbox("📍 Filter by City:", ["All"] + sorted(available_cities))

    available_skills = sorted(set(
        skill.strip() for skills in df["Skills"] if skills != "N/A"
        for skill in skills.split(",")
    ))
    selected_skill = st.selectbox("🛠 Filter by Skill:", ["All"] + available_skills)

    # Apply Filters
    filtered_df = df.copy()
    if selected_city != "All":
        filtered_df = filtered_df[filtered_df["Location"] == selected_city]
    if selected_skill != "All":
        filtered_df = filtered_df[filtered_df["Skills"].str.contains(selected_skill)]

    st.success(f"Showing {len(filtered_df)} jobs after filtering.")
    st.markdown("### 📋 Filtered Job Listings")
    st.write(filtered_df.to_markdown(index=False), unsafe_allow_html=True)

    # ------------------ Charts ------------------
    st.markdown("## 📊 Job Market Insights")

    if not filtered_df.empty:
        # Top Cities
        top_cities = filtered_df["Location"].value_counts().head(10)
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_cities.values, y=top_cities.index, ax=ax1, palette="coolwarm")
        ax1.set_title("Top Job Locations")
        ax1.set_xlabel("Job Count")
        ax1.set_ylabel("City")
        st.pyplot(fig1)

        # Top Titles
        top_titles = filtered_df["Job Title"].value_counts().head(10)
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        sns.barplot(x=top_titles.values, y=top_titles.index, ax=ax2, palette="light:#5A9")
        ax2.set_title("Most Common Job Titles")
        st.pyplot(fig2)

        # Top Skills
        all_skills = []
        for s in filtered_df["Skills"]:
            if s != "N/A":
                all_skills.extend([x.strip() for x in s.split(",")])
        skill_series = pd.Series(all_skills).value_counts().head(10)
        if not skill_series.empty:
            fig3, ax3 = plt.subplots(figsize=(8, 5))
            skill_series = skill_series.sort_values(ascending=True)
            sns.barplot(x=skill_series.values, y=skill_series.index, ax=ax3, palette="viridis")
            ax3.set_title("Top Required Skills")
            st.pyplot(fig3)

        # Top Companies
        top_companies = filtered_df["Company"].value_counts().head(10)
        if not top_companies.empty:
            fig4, ax4 = plt.subplots(figsize=(8, 5))
            sns.barplot(x=top_companies.values, y=top_companies.index, ax=ax4, palette="crest")
            ax4.set_title("Top Companies Hiring")
            ax4.set_xlabel("Number of Jobs")
            ax4.set_ylabel("Company")
            st.pyplot(fig4)

        # Job Trend
        trend_df = filtered_df.groupby("Posted").size().reset_index(name="Job Count")
        fig5, ax5 = plt.subplots(figsize=(8, 5))
        sns.lineplot(data=trend_df, x="Posted", y="Job Count", marker="o", ax=ax5)
        ax5.set_title("Job Posting Trend Over Time")
        st.pyplot(fig5)

        # Forecasting
        st.markdown("## 🔮 Job Forecast (Next 7 Days)")
        prophet_df = trend_df.rename(columns={"Posted": "ds", "Job Count": "y"})
        model = Prophet()
        model.fit(prophet_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        fig6 = model.plot(forecast)
        st.pyplot(fig6)

    else:
        st.warning("No data available after filtering.")