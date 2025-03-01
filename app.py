import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with author affiliations.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type="csv")

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

# Exclusion keywords to filter out unwanted entries
exclusion_keywords = [
    "College", "Affiliated to", "Rajarambapu Institute of Technology",
    "Bhogawati Mahavidyalaya", "ADCET", "AMGOI",
    "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions",
    "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"
]

# Regex patterns to help capture department names with alternative formats
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

# Function to extract department(s) from an affiliation text.
# 1. Check exclusion keywords first.
# 2. Then, look for valid department names.
# 3. If the affiliation is from Shivaji University, return all found names; otherwise, only the first.
def extract_department(affiliation_text):
    if pd.isna(affiliation_text) or not isinstance(affiliation_text, str):
        return "Other"
    
    affil_lower = affiliation_text.lower()

    # Step 1: Apply exclusion filter.
    for exclusion in exclusion_keywords:
        if exclusion.lower() in affil_lower:
            return "Other"
    
    # Determine if the affiliation is from Shivaji University.
    is_shivaji = "shivaji university" in affil_lower

    found_departments = []
    
    # Step 2: Exact matching from the valid_departments list.
    for dept in valid_departments:
        if dept.lower() in affil_lower:
            if dept not in found_departments:
                found_departments.append(dept)
    
    # Step 3: Regex-based matching for alternative formats.
    for dept, patterns in department_patterns.items():
        for pattern in patterns:
            if re.search(pattern, affil_lower, re.IGNORECASE):
                if dept not in found_departments:
                    found_departments.append(dept)
    
    if not found_departments:
        return "Other"
    
    # Step 4: For Shivaji University, join all found department names.
    if is_shivaji:
        return "; ".join(found_departments)
    else:
        # For other universities, return only the first found match.
        return found_departments[0]

# Function to process the CSV file.
def process_file(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None
    
    # Determine the correct column for affiliations.
    affil_column = None
    for col in ["Affiliations", "Authors with affiliations"]:
        if col in df.columns:
            affil_column = col
            break
    if not affil_column:
        st.error("CSV must contain either 'Affiliations' or 'Authors with affiliations' column.")
        return None
    
    # Apply the extraction function.
    df["Department"] = df[affil_column].apply(extract_department)
    
    st.write("### Debug Output (First 10 Rows)")
    st.write(df[[affil_column, "Department"]].head(10))
    
    return df

# Function to compute department statistics.
# If the "Department" column has multiple names (separated by ";"), count each separately.
def process_department_stats(df):
    stats = {dept: {"Papers": 0} for dept in valid_departments}
    stats["Other"] = {"Papers": 0}
    
    for _, row in df.iterrows():
        dept_field = row["Department"]
        if dept_field == "Other":
            stats["Other"]["Papers"] += 1
        else:
            # Split multiple departments and count each.
            dept_list = [d.strip() for d in dept_field.split(";")]
            for dept in dept_list:
                if dept in stats:
                    stats[dept]["Papers"] += 1
                else:
                    stats["Other"]["Papers"] += 1
    return pd.DataFrame([{"Department": dept, "Papers": data["Papers"]} for dept, data in stats.items()])

# Process the file if uploaded.
if uploaded_file:
    processed_df = process_file(uploaded_file)
    if processed_df is not None:
        st.header("Processed Affiliation Data")
        st.dataframe(processed_df)
        
        stats_df = process_department_stats(processed_df)
        st.header("Department Statistics")
        st.dataframe(stats_df)
        st.bar_chart(stats_df.set_index("Department")["Papers"])
        
        # Export results to an Excel file with two sheets.
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
