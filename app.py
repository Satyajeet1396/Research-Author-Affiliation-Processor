import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64
import re

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with details on authors (with affiliations) and citation counts.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# Valid affiliations
valid_affiliations = ["Shivaji University", "Saveetha University"]

# Exclusion keywords
exclusion_keywords = ["College", "Affiliated to", "Rajarambapu Institute of Technology", "Bhogawati Mahavidyalaya", 
                      "ADCET", "AMGOI", "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions", 
                      "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"]

# Valid departments
valid_departments = [
    "Department of Agrochemicals and Pest Management", "Department of Bio-Chemistry",
    "Department of Bio-Technology", "Department of Botany", "Department of Chemistry",
    "Department of Commerce and Management", "Department of Commerce and Management M.B.A. Unit",
    "Department of Computer Science", "Department of Economics", "FE Department of Education",
    "Department of Electronics", "Department of English", "Department of Environmental Science",
    "Department of Food Science and Technology", "Department of Foreign Languages",
    "Department of Geography", "Department of Hindi", "Department of History",
    "Department of Journalism and Mass Communication", "Department of Law",
    "Department of Library and Information Science", "Department of Lifelong Learning and Extension",
    "Department of Marathi", "Department of Mathematics", "Department of Mass Communication",
    "Department of Microbiology", "Department of Music and Dramatics", "Department of Physics",
    "FE Department of Political Science", "Department of Psychology", "Department of Sociology",
    "Department of Sports", "Department of Statistics", "Department of Technology",
    "Department of Zoology", "School of Nanoscience and Biotechnology",
    "Department of Biochemistry", "Department of Biotechnology",
    "Yashwantrao Chavan School of Rural Development", "UGC Center For Coaching For Competitive Examinations UGC Center"
]

# Department consolidation mapping (case-insensitive regex patterns)
consolidation_map = {
    "School of Nanoscience and Biotechnology": [
        r"school\s+of\s+nanoscience\s+(and|\&)?\s*biotechnology",
        r"school\s+of\s+nanoscience\s+and\s+technology",
        r"department\s+of\s+nanoscience\s*&\s*(biotechnology|nanotechnology)"
    ],
    "Department of Chemistry": [
        r"chemistry\s+department",
        r"analytical\s+chemistry\s+laboratory",
        r"dept\.?\s+of\s+chemistry"
    ],
    "Department of Physics": [
        r"physics\s+department",
        r"dept\.?\s+of\s+phys\.?",
        r"shivaji\s+univ\b"
    ]
}

# Function to extract departments from an affiliation string
def extract_departments(affiliation_str):
    segments = affiliation_str.split(";")
    matching_departments = []

    for seg in segments:
        seg_clean = seg.strip().lower()
        if not any(valid.lower() in seg_clean for valid in valid_affiliations):
            continue
        if any(excl.lower() in seg_clean for excl in exclusion_keywords):
            continue

        # Step 1: Check for consolidated departments using regex
        added_consolidated = []
        for target_dept, patterns in consolidation_map.items():
            for pattern in patterns:
                if re.search(pattern, seg_clean, re.IGNORECASE):
                    if target_dept not in matching_departments:
                        matching_departments.append(target_dept)
                        added_consolidated.append(target_dept)
                        break  

        # Step 2: Check for other valid departments
        for dept in valid_departments:
            dept_lower = dept.lower()
            if dept_lower in seg_clean or re.search(rf"\b{dept_lower}\b", seg_clean, re.IGNORECASE):
                if dept not in added_consolidated and dept not in matching_departments:
                    matching_departments.append(dept)

    return "; ".join(matching_departments) if matching_departments else "Other"

# Process file function
def process_file(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None

    # Determine column to use for affiliations
    affil_field = "Affiliations" if "Affiliations" in df.columns else "Authors with affiliations" if "Authors with affiliations" in df.columns else None
    if not affil_field:
        st.error("CSV must contain either an 'Affiliations' or 'Authors with affiliations' column.")
        return None

    df["Department"] = df[affil_field].apply(extract_departments)
    return df

# Process department statistics
def process_department_stats(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None

    affil_field = "Affiliations" if "Affiliations" in df.columns else "Authors with affiliations" if "Authors with affiliations" in df.columns else None
    if not affil_field:
        st.error("CSV must contain either an 'Affiliations' or 'Authors with affiliations' column.")
        return None

    df["Cited by"] = df.get("Cited by", 0)

    stats = {dept: {"Papers": 0, "Citations": 0} for dept in valid_departments}
    stats["Other"] = {"Papers": 0, "Citations": 0}

    for _, row in df.iterrows():
        affil_text = row[affil_field]
        citations = float(row["Cited by"]) if pd.notnull(row["Cited by"]) else 0

        segments = affil_text.split(";")
        found = False
        for seg in segments:
            seg_clean = seg.strip()
            if not any(valid.lower() in seg_clean.lower() for valid in valid_affiliations):
                continue
            if any(excl.lower() in seg_clean.lower() for excl in exclusion_keywords):
                continue
            for dept in valid_departments:
                if dept.lower() in seg_clean.lower():
                    stats[dept]["Papers"] += 1
                    stats[dept]["Citations"] += citations
                    found = True
        if not found:
            stats["Other"]["Papers"] += 1
            stats["Other"]["Citations"] += citations

    return pd.DataFrame([{"Department": dept, "Papers": data["Papers"], "Citations": data["Citations"]} for dept, data in stats.items()])

# Process file if uploaded
if uploaded_file:
    processed_df = process_file(uploaded_file)
    stats_df = process_department_stats(uploaded_file)
else:
    processed_df = None
    stats_df = None

st.header("Processed Affiliation Data")
if processed_df is not None:
    st.dataframe(processed_df)

st.header("Department Statistics")
if stats_df is not None:
    st.dataframe(stats_df)
    st.bar_chart(stats_df.set_index("Department")["Papers"])
    st.bar_chart(stats_df.set_index("Department")["Citations"])

# Export to Excel
if processed_df is not None and stats_df is not None:
    towrite = BytesIO()
    with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
        processed_df.to_excel(writer, sheet_name="Affiliations", index=False)
        stats_df.to_excel(writer, sheet_name="Statistics", index=False)
    towrite.seek(0)
    st.download_button("Download Processed Data", data=towrite, file_name="processed_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
