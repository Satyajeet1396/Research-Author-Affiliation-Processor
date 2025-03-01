import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with author affiliations.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# List of valid departments (names must match your expected output)
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

# Exclusion keywords – if a segment contains any of these, it is ignored.
exclusion_keywords = [
    "College", "Affiliated to", "Mahavidyalaya", "Rajarambapu Institute of Technology",
    "ADCET", "AMGOI", "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions",
    "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"
]

# Regex patterns for alternative formats for some departments
department_patterns = {
    "School of Nanoscience and Biotechnology": [
        r"school\s+of\s+nanoscience\s*(and|&)?\s*(technology|biotechnology|bio[\s-]?tech)",
        r"nanoscience\s*(and|&)?\s*(technology|biotechnology|bio[\s-]?tech)\s+school",
        r"department\s+of\s+nanoscience\s*[&]?\s*(technology|biotechnology|bio[\s-]?tech)"
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

def extract_department(affiliation_text):
    if pd.isna(affiliation_text) or not isinstance(affiliation_text, str):
        return "Other"
    
    segments = affiliation_text.split(";")
    shivaji_depts = []
    
    for seg in segments:
        seg_lower = seg.lower().strip()
        norm_seg = seg_lower.replace("-", " ")
        
        # Skip segments with exclusion keywords
        if any(excl.lower() in norm_seg for excl in exclusion_keywords):
            continue
        
        # Process segments mentioning "shivaji university"
        if "shivaji university" in norm_seg:
            found = []
            
            # Exact matching
            for dept in valid_departments:
                norm_dept = dept.lower().replace("-", " ")
                if norm_dept in norm_seg and dept not in found:
                    found.append(dept)
            
            # Regex matching (with priority)
            for dept, patterns in department_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, norm_seg, re.IGNORECASE) and dept not in found:
                        found.append(dept)
            
            shivaji_depts.extend(found)
    
    return "; ".join(list(dict.fromkeys(shivaji_depts))) if shivaji_depts else "Other"

def process_file(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None
    
    # Identify affiliation column
    affil_column = None
    for col in ["Affiliations", "Authors with affiliations"]:
        if col in df.columns:
            affil_column = col
            break
    if not affil_column:
        st.error("CSV must contain either 'Affiliations' or 'Authors with affiliations' column.")
        return None
    
    df["Department"] = df[affil_column].apply(extract_department)
    
    return df

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
