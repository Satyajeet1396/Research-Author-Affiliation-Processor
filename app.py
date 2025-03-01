import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64

st.title("Research Author Affiliation & Department Statistics Processor")
st.write("Upload a CSV file containing research papers with details on authors (with affiliations) and citation counts.")

# File uploader (shared between modules)
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# Valid affiliations (used for both corresponding author extraction and department filtering)
valid_affiliations = ["Shivaji University", "Saveetha University"]

# Exclusion keywords to skip in affiliation segments (exact capitalization as given)
exclusion_keywords = ["College", "Affiliated to", "Rajarambapu Institute of Technology", "Bhogawati Mahavidyalaya", "ADCET", "AMGOI", "Ashokrao Mane Group of Institutes", "Sanjay Ghodawat Group of Institutions", "Patangrao Kadam", "Centre for PG Studies", "D. Y. Patil Education Society"]

# Valid department names to look for
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

# Helper function to extract department(s) from an affiliation string.
# Only segments that contain one of the valid affiliations and do NOT contain any exclusion keyword are considered.
def extract_departments(affiliation_str):
    segments = affiliation_str.split(";")
    matching_departments = []
    for seg in segments:
        seg_clean = seg.strip()
        if not any(valid_affil.lower() in seg_clean.lower() for valid_affil in valid_affiliations):
            continue
        if any(excl.lower() in seg_clean.lower() for excl in exclusion_keywords):
            continue
        for dept in valid_departments:
            if dept.lower() in seg_clean.lower():
                if dept in [
                    "School of Nanoscience", "School of Nanoscience and Technology", "Department of Nanoscience & Nanotechnology", "School of Nanoscience & Biotechnology", "School of Nanoscience & Technology", "School of Nanoscience and Bio-Technology"
                    ]:
                    if "School of Nanoscience and Biotechnology" not in matching_departments:
                        matching_departments.append("School of Nanoscience and Biotechnology")
        for dept in valid_departments:
            if dept.lower() in seg_clean.lower():
                if dept in [
                    "Chemistry Department", "Analytical Chemistry Laboratory", "Dept. of Chemistry"
                    ]:
                    if "Department of Chemistry" not in matching_departments:
                        matching_departments.append("Department of Chemistry")
        for dept in valid_departments:
            if dept.lower() in seg_clean.lower():
                if dept in [
                    "Physics Department", "Air Glass Laboratory", "Dept. of Phys.", "Dept. of Physics", "Shivaji Univ", "Dept. Phys."
                    ]:
                    if "Department of Physics" not in matching_departments:
                        matching_departments.append("Department of Physics")    
                else:
                    if dept not in matching_departments:
                        matching_departments.append(dept)
    return "; ".join(matching_departments) if matching_departments else "Other"

# Affiliation Processor: Extract corresponding author info and create a new "Department" column.
def process_file(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None

    # Determine which column to use for affiliation data.
    if "Affiliations" in df.columns:
        affil_field = "Affiliations"
    elif "Authors with affiliations" in df.columns:
        affil_field = "Authors with affiliations"
    else:
        st.error("CSV must contain either an 'Affiliations' or 'Authors with affiliations' column.")
        return None

    # Extract corresponding author and affiliation.
    df['Corresponding Author'] = ""
    df['Corresponding Affiliation'] = ""
    for index, row in df.iterrows():
        affil_text = row[affil_field]
        parts_list = affil_text.split(";")
        valid_authors = []
        for part in parts_list:
            # Expecting format: "Name, Affiliation"
            components = part.strip().split(',', 1)
            if len(components) == 2:
                name, affiliation = components
                affiliation = affiliation.strip()
                # Special handling for Saveetha University.
                if "Saveetha University" in affiliation:
                    if "Saveetha University" in valid_affiliations:
                        valid_authors.append((name.strip(), affiliation))
                # Otherwise, check if the affiliation contains a valid affiliation and does NOT contain an exclusion keyword.
                elif any(valid in affiliation for valid in valid_affiliations):
                    if not any(excl.lower() in affiliation.lower() for excl in exclusion_keywords):
                        valid_authors.append((name.strip(), affiliation))
        if valid_authors:
            corresponding_author, corresponding_affiliation = valid_authors[-1]
            df.at[index, 'Corresponding Author'] = corresponding_author
            df.at[index, 'Corresponding Affiliation'] = corresponding_affiliation

    # Create the new "Department" column based on the selected affiliation field.
    df["Department"] = df[affil_field].apply(extract_departments)
    return df

# Department Statistics: Tally number of papers and total citations for each department.
def process_department_stats(file):
    file.seek(0)
    try:
        df = pd.read_csv(file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty. Please upload a valid CSV file with data.")
        return None

    # Determine which column to use for affiliation data.
    if "Affiliations" in df.columns:
        affil_field = "Affiliations"
    elif "Authors with affiliations" in df.columns:
        affil_field = "Authors with affiliations"
    else:
        st.error("CSV must contain either an 'Affiliations' or 'Authors with affiliations' column.")
        return None

    # Use the "Cited by" column for citation counts; default to 0 if missing.
    if "Cited by" not in df.columns:
        df["Cited by"] = 0

    # Initialize statistics dictionary for each valid department and an "Other" bucket.
    stats = {dept: {"Papers": 0, "Citations": 0} for dept in valid_departments}
    stats["Other"] = {"Papers": 0, "Citations": 0}

    # Process each paper (row) to tally counts.
    for index, row in df.iterrows():
        affil_text = row[affil_field]
        citations = row["Cited by"]
        try:
            citations = float(citations)
        except:
            citations = 0

        segments = affil_text.split(";")
        found = False
        for seg in segments:
            seg_clean = seg.strip()
            # Only consider the segment if it contains one of the valid affiliations.
            if not any(valid_affil.lower() in seg_clean.lower() for valid_affil in valid_affiliations):
                continue
            # Skip segments that contain any exclusion keyword.
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

    stats_df = pd.DataFrame([
        {"Department": dept, "Papers": data["Papers"], "Citations": data["Citations"]}
        for dept, data in stats.items()
    ])
    return stats_df

# Process file if uploaded.
if uploaded_file:
    processed_df = process_file(uploaded_file)
    stats_df = process_department_stats(uploaded_file)
else:
    processed_df = None
    stats_df = None

# Display both outputs on the same page.
st.header("Affiliation Processor Output")
if processed_df is not None:
    st.dataframe(processed_df)
else:
    st.info("No processed data to show. Please upload a CSV file.")

st.header("Department Statistics Output")
if stats_df is not None:
    st.dataframe(stats_df)
    st.markdown("### Papers Published (per Department)")
    st.bar_chart(stats_df.set_index("Department")["Papers"])
    st.markdown("### Total Citations (per Department)")
    st.bar_chart(stats_df.set_index("Department")["Citations"])
else:
    st.info("No statistics to show. Please upload a CSV file.")

# Export both outputs to a single Excel file with two sheets.
if processed_df is not None and stats_df is not None:
    towrite = BytesIO()
    with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
        processed_df.to_excel(writer, sheet_name="Affiliations", index=False)
        stats_df.to_excel(writer, sheet_name="Statistics", index=False)
    towrite.seek(0)
    st.download_button(
        label="Download Excel File (2 Sheets)",
        data=towrite,
        file_name="processed_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.info("Created by Dr. Satyajeet Patil")
st.info("For more cool apps like this visit: https://patilsatyajeet.wixsite.com/home/python")

with st.expander("🤝 Support Our Research", expanded=False):
    st.markdown("""
    <div style='text-align: center; padding: 1rem; background-color: #f0f2f6; border-radius: 10px; margin: 1rem 0;'>
        <h3>🙏 Your Support Makes a Difference!</h3>
        <p>Your contribution helps us continue developing free tools for the research community.</p>
        <p>Every donation, no matter how small, fuels our research journey!</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### UPI Payment")
        def generate_qr_code(data):
            qr = qrcode.make(data)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer
        upi_url = "upi://pay?pa=satyajeet1396@oksbi&pn=Satyajeet Patil&cu=INR"
        buffer = generate_qr_code(upi_url)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        st.markdown("Scan to pay: **satyajeet1396@oksbi**")
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; align-items: center;">
                <img src="data:image/png;base64,{qr_base64}" width="200">
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown("#### Buy Me a Coffee")
        st.markdown("Support through Buy Me a Coffee platform:")
        st.markdown(
            """
            <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                <a href="https://www.buymeacoffee.com/researcher13" target="_blank">
                    <img src="https://img.buymeacoffee.com/button-api/?text=Support our Research&emoji=&slug=researcher13&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff" alt="Support our Research"/>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
st.info("A small donation from you can fuel our research journey, turning ideas into breakthroughs that can change lives!")
