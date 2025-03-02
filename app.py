import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with author affiliations.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# Predefined valid departments
valid_departments = {
    "Department of Agro-Chemicals and Pest Management", "Department of Bio-Chemistry",
    "Department of Bio-Technology", "Department of Botany", "Department of Chemistry",
    "Department of Commerce and Management", "Department of Computer Science",
    "Department of Electronics", "Department of Environmental Science",
    "Department of Geography", "Department of History", "Department of Law",
    "Department of Marathi", "Department of Mathematics", "Department of Microbiology",
    "Department of Music and Dramatics", "Department of Physics",
    "Department of Political Science", "Department of Psychology", "Department of Sociology",
    "Department of Statistics", "Department of Technology", "Department of Zoology",
    "School of Nanoscience and Biotechnology"
}

# Exclusion keywords
exclusion_keywords = {
    "College", "Affiliated to", "Mahavidyalaya", "Rajarambapu Institute of Technology",
    "ADCET", "AMGOI", "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions",
    "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"
}

# Regex patterns for department recognition
department_patterns = {
    "School of Nanoscience and Biotechnology": [
        r"(school|department)\s+of\s+nanoscience\s+(and|\&)\s*(technology|biotechnology)"
    ],
    "Department of Chemistry": [
        r"chemistry\s+department", r"dept\.?\s+of\s+chemistry"
    ],
    "Department of Physics": [
        r"physics\s+department", r"dept\.?\s+of\s+physics"
    ]
}

# Extract department information from affiliation
def extract_department(affiliation_text):
    if not isinstance(affiliation_text, str) or pd.isna(affiliation_text):
        return "Other"

    departments = set()
    for segment in affiliation_text.lower().replace("-", " ").split(";"):
        segment = segment.strip()

        # Skip segment if any exclusion keyword is found
        if any(excl.lower() in segment for excl in exclusion_keywords):
            continue

        # Process only segments containing "shivaji university"
        if "shivaji university" in segment:
            # Exact matching
            for dept in valid_departments:
                if dept.lower().replace("-", " ") in segment:
                    departments.add(dept)

            # Regex matching
            for dept, patterns in department_patterns.items():
                if any(re.search(pattern, segment, re.IGNORECASE) for pattern in patterns):
                    departments.add(dept)

    return "; ".join(departments) if departments else "Other"

# Process CSV file
def process_file(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None

    # Identify affiliation column
    affil_column = next((col for col in ["Affiliations", "Authors with affiliations"] if col in df.columns), None)
    if not affil_column:
        st.error("CSV must contain either 'Affiliations' or 'Authors with affiliations' column.")
        return None

    df["Department"] = df[affil_column].apply(extract_department)
    
    st.write("### Debug Output (First 10 Rows)")
    st.write(df[[affil_column, "Department"]].head(10))

    return df

# Compute department statistics efficiently
def process_department_stats(df):
    all_departments = df["Department"].str.split(";").explode().str.strip()
    stats = all_departments.value_counts().reset_index()
    stats.columns = ["Department", "Papers"]
    return stats

# Process and display results
if uploaded_file:
    processed_df = process_file(uploaded_file)
    if processed_df is not None:
        st.header("Processed Affiliation Data")
        st.dataframe(processed_df)

        stats_df = process_department_stats(processed_df)
        st.header("Department Statistics")
        st.dataframe(stats_df)
        st.bar_chart(stats_df.set_index("Department")["Papers"])

        # Export results to Excel
        towrite = BytesIO()
        with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
            processed_df.to_excel(writer, sheet_name="Affiliations", index=False)
            stats_df.to_excel(writer, sheet_name="Statistics", index=False)
        towrite.seek(0)

        st.download_button(
            "Download Processed Data",
            data=towrite,
            file_name="processed_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
