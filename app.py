import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with author affiliations.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# List of valid departments (ensure the names match your expected output)
valid_departments = [
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
]

# Updated exclusion keywords: any segment containing these strings will be skipped.
exclusion_keywords = [
    "College", "Affiliated to", "Mahavidyalaya", "Rajarambapu Institute of Technology",
    "ADCET", "AMGOI", "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions",
    "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"
]

# Regex patterns for alternative formats for some departments
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
# 1. Split the text into segments (by semicolon).
# 2. For each segment, first apply the exclusion filter.
# 3. Then, extract valid department names (using both exact and regex matching),
#    normalizing hyphens.
# 4. If any segment is from Shivaji University, return all departments from those segments.
#    Otherwise, return the first valid department from the other segments.
def extract_department(affiliation_text):
    if pd.isna(affiliation_text) or not isinstance(affiliation_text, str):
        return "Other"
    
    segments = affiliation_text.split(";")
    shivaji_depts = []
    other_depts = []
    
    for seg in segments:
        seg_lower = seg.lower().strip()
        # Normalize hyphens to spaces (e.g., "agro-chemicals" becomes "agro chemicals")
        norm_seg = seg_lower.replace("-", " ")
        
        # Apply exclusion filter: skip segments containing any exclusion keyword.
        excluded = False
        for exclusion in exclusion_keywords:
            if exclusion.lower() in norm_seg:
                excluded = True
                break
        if excluded:
            continue
        
        found = []
        # Exact matching (normalize both sides)
        for dept in valid_departments:
            norm_dept = dept.lower().replace("-", " ")
            if norm_dept in norm_seg:
                if dept not in found:
                    found.append(dept)
        
        # Regex matching for alternative formats
        for dept, patterns in department_patterns.items():
            for pattern in patterns:
                if re.search(pattern, norm_seg, re.IGNORECASE):
                    if dept not in found:
                        found.append(dept)
        
        # Check if the segment is from Shivaji University
        if "shivaji university" in norm_seg:
            shivaji_depts.extend(found)
        else:
            other_depts.extend(found)
    
    # If any departments are found from segments of Shivaji University, return them (unique, joined by "; ")
    if shivaji_depts:
        unique_shivaji = []
        for dept in shivaji_depts:
            if dept not in unique_shivaji:
                unique_shivaji.append(dept)
        return "; ".join(unique_shivaji) if unique_shivaji else "Other"
    else:
        # Otherwise, if any departments were found in non-Shivaji segments, return the first valid one.
        if other_depts:
            return other_depts[0]
        else:
            return "Other"

# Process the CSV file and add a new "Department" column based on the affiliation extraction.
def process_file(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None
    
    affil_column = None
    for col in ["Affiliations", "Authors with affiliations"]:
        if col in df.columns:
            affil_column = col
            break
    if not affil_column:
        st.error("CSV must contain either 'Affiliations' or 'Authors with affiliations' column.")
        return None
    
    df["Department"] = df[affil_column].apply(extract_department)
    
    st.write("### Debug Output (First 10 Rows)")
    st.write(df[[affil_column, "Department"]].head(10))
    
    return df

# Process department statistics:
# If the "Department" field contains multiple names (separated by ";"), count each separately.
def process_department_stats(df):
    stats = {dept: {"Papers": 0} for dept in valid_departments}
    stats["Other"] = {"Papers": 0}
    
    for _, row in df.iterrows():
        dept_field = row["Department"]
        if dept_field == "Other":
            stats["Other"]["Papers"] += 1
        else:
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
