import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with author affiliations.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# Define valid affiliations
valid_affiliations = ["Shivaji University", "Saveetha University"]

# Define exclusion keywords
exclusion_keywords = [
    "College", "Affiliated to", "Rajarambapu Institute of Technology",
    "Bhogawati Mahavidyalaya", "ADCET", "AMGOI",
    "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions",
    "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"
]

# List of valid departments
valid_departments = [
    "Department of Agrochemicals and Pest Management", "Department of Bio-Chemistry",
    "Department of Bio-Technology", "Department of Botany", "Department of Chemistry",
    "Department of Commerce and Management", "Department of Computer Science",
    "Department of Electronics", "Department of Environmental Science",
    "Department of Geography", "Department of History", "Department of Law",
    "Department of Marathi", "Department of Mathematics", "Department of Microbiology",
    "Department of Music and Dramatics", "Department of Physics",
    "Department of Political Science", "Department of Psychology", "Department of Sociology",
    "Department of Statistics", "Department of Technology", "Department of Zoology",
    "School of Nanoscience and Biotechnology"
]

# **Fix: Consolidation mapping for regex**
department_patterns = {
    "School of Nanoscience and Biotechnology": [
        r"school\s+of\s+nanoscience\s+(and|\&)?\s*biotechnology",
        r"nanoscience\s+(and|\&)?\s*biotechnology\s+school",
        r"department\s+of\s+nanoscience\s*\&?\s*biotechnology"
    ],
    "Department of Chemistry": [
        r"chemistry\s+department",
        r"dept\.?\s+of\s+chemistry"
    ],
    "Department of Physics": [
        r"physics\s+department",
        r"dept\.?\s+of\s+physics"
    ]
}

# Function to extract department
def extract_department(affiliation_text):
    if pd.isna(affiliation_text) or not isinstance(affiliation_text, str):
        return "Other"

    affiliation_text = affiliation_text.lower()  # Convert to lowercase
    for exclusion in exclusion_keywords:
        if exclusion.lower() in affiliation_text:
            return "Other"

    # **First: Try exact matching**
    for dept in valid_departments:
        if dept.lower() in affiliation_text:
            return dept  # **Return exact match immediately**

    # **Second: Try regex matching for consolidated departments**
    for dept, patterns in department_patterns.items():
        for pattern in patterns:
            if re.search(pattern, affiliation_text, re.IGNORECASE):
                return dept  # **Return regex matched department**

    return "Other"  # Default to Other if nothing matches

# Function to process the file
def process_file(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None

    # Check for valid column names
    affil_column = None
    for col in ["Affiliations", "Authors with affiliations"]:
        if col in df.columns:
            affil_column = col
            break

    if not affil_column:
        st.error("CSV must contain either 'Affiliations' or 'Authors with affiliations' column.")
        return None

    # Apply department extraction function
    df["Department"] = df[affil_column].apply(extract_department)

    # Debugging: Print department matches
    st.write("### Debugging Output - First 10 Rows")
    st.write(df[[affil_column, "Department"]].head(10))  # Show the first 10 rows

    return df

# Function to process department statistics
def process_department_stats(df):
    stats = {dept: {"Papers": 0} for dept in valid_departments}
    stats["Other"] = {"Papers": 0}

    for _, row in df.iterrows():
        department = row["Department"]
        if department in stats:
            stats[department]["Papers"] += 1
        else:
            stats["Other"]["Papers"] += 1

    return pd.DataFrame([{"Department": dept, "Papers": data["Papers"]} for dept, data in stats.items()])

# **Process the file**
if uploaded_file:
    processed_df = process_file(uploaded_file)
    if processed_df is not None:
        st.header("Processed Data")
        st.dataframe(processed_df)

        # Generate stats
        stats_df = process_department_stats(processed_df)

        st.header("Department Statistics")
        st.dataframe(stats_df)
        st.bar_chart(stats_df.set_index("Department")["Papers"])

        # Export to Excel
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
