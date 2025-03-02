import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with author affiliations.")

# File uploader
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# Standardized list of valid departments
valid_departments = {
    "Department of Agro-Chemicals and Pest Management", "Department of Bio-Chemistry",
    "Department of Bio-Technology", "Department of Botany", "Department of Chemistry",
    "Department of Commerce and Management", "Department of Computer Science",
    "Department of Electronics", "Department of Environmental Science",
    "Department of Geography", "Department of History", "Department of Law",
    "Department of Marathi", "Department of Mathematics", "Department of Microbiology",
    "Department of Music and Dramatics", "Department of Physics", "Department of Biotechnology"
    "Department of Political Science", "Department of Psychology", "Department of Sociology",
    "Department of Statistics", "Department of Technology", "Department of Zoology",
    "University Science Instrumentation Centre", "School of Nanoscience and Biotechnology", "Department of Library & Information Science"
}

# Normalize variations for better detection
department_aliases = {
    # Mathematics
    "Mathematics Department": "Department of Mathematics",
    
    # Department of Library & Information Science
    "Barr.Balasaheb Khardekar Library": "Department of Library & Information Science",
    
    # Electronics
    "Dept. of Electronics": "Department of Electronics",
    "Department of Electronic": "Department of Electronics",
    
    # Zoology
    "Zoology Department": "Department of Zoology",
    "Dept. of Zoology": "Department of Zoology",
    
    # Botany
    "Botany Department": "Department of Botany",
    "Dept of Botany": "Department of Botany",
    "Botany Dept": "Department of Botany",
    
    # Chemistry
    "Analytical Chemistry Laboratory": "Department of Chemistry",
    "Inorganic Chemistry Laboratories": "Department of Chemistry",
    "Deptt. of Chemistry": "Department of Chemistry",
    "Department of C hemistry": "Department of Chemistry",
    "Analytical Chemistry and Material Science Research Laboratory": "Department of Chemistry",
    "Department of Organic Chemistry": "Department of Chemistry",
    "Department of Chemistr": "Department of Chemistry",
    "Depatment of Chemistry": "Department of Chemistry",
    "Kinetics and Catalysis Division": "Department of Chemistry",
    "Analyt. Chem. Lab.": "Department of Chemistry",
    
    # Physics
    "Materials Research Laboratory Department": "Department of Physics",
    "Departmentof Physics, Shivaji University": "Department of Physics",
    "Department of Phhysics, Shivaji University, Kolhapur, M.S., 416004, India": "Department of Physics",
    "Air Glass Laboratory": "Department of Physics",
    "Air Glass Laboratory, Dept. Phys.": "Department of Physics",
    "Department O F Physics": "Department of Physics",
    "Depertment of Physics": "Department of Physics",
    "Deptartment of Physics": "Department of Physics",
    "Thin Film Materials Laboratory": "Department of Physics",
    "Dept. Phys.": "Department of Physics",
    "Physica Department": "Department of Physics",
    "Solid State Physics Research Laboratory": "Department of Physics",
    
    # Technology
    "Dept. of Energy Technology": "Department of Technology",
    "Department of Energy Technology": "Department of Technology",
    "Department of Mechanical Engineering": "Department of Technology",
    "Department of Compute RScience and Engineering": "Department of Technology",
    "Department of Civil Engineering": "Department of Technology",
    "Electronics Engineering": "Department of Technology",
    
    # USIC
    "Vacuum Techniques and Thin Film Laboratory": "University Science Instrumentation Centre",
    "University Science Instrumentation Centre(USIC)": "University Science Instrumentation Centre",
    
    # Agro-Chemicals
    "Department of Agrochemical and Pest Management": "Department of Agro-Chemicals and Pest Management",
    
    # Nanoscience
    "Computational Electronics and Nanoscience Research Laboratory": "School of Nanoscience and Biotechnology",
    "School of Nano Science and Technology": "School of Nanoscience and Biotechnology",
    "Department of Nanoscience & Nanotechnology": "School of Nanoscience and Biotechnology",
    
    # Biochemistry
    "Deartment of Biochemistry": "Department of Bio-Chemistry",
    "Deparment of Biochemistry": "Department of Bio-Chemistry",
    "Dept. of Biochemistry": "Department of Bio-Chemistry",
    
    # Statistics
    "Dept. of Statistics": "Department of Statistics",
    "Department of Statisties": "Department of Statistics"
}

# Exclusion keywords
exclusion_keywords = {
    "College", "Affiliated to", "Mahavidyalaya", "Rajarambapu Institute of Technology",
    "ADCET", "AMGOI", "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions",
    "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"
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

        # Check for exact matches
        for dept in valid_departments:
            if dept.lower().replace("-", " ") in segment:
                departments.add(dept)

        # Check for alias matches
        for alias, standard_dept in department_aliases.items():
            if alias.lower().replace("-", " ") in segment:
                departments.add(standard_dept)

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
