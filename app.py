import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64

st.title("Research Author Affiliation and Department Statistics Processor")
st.write("Upload a CSV file containing research papers with details on authors (with affiliations) and citation counts.")

# File uploader (shared between modules)
uploaded_file = st.file_uploader("Upload CSV", type="csv")

# Valid affiliations (for extracting corresponding author)
valid_affiliations = ["Shivaji University", "Saveetha University"]

# Exclusion keywords to skip in affiliation segments (using exact capitalization in the list)
exclusion_keywords = ["College", "Affiliated to"]

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
    "Department of Zoology", "School of Nanoscience and Technology", "School of Nanoscience and Biotechnology",
    "Department of Biochemistry", "Department of Biotechnology",
    "Yashwantrao Chavan School of Rural Development", "UGC Center For Coaching For Competitive Examinations UGC Center"
]

# Helper function to extract department(s) from an affiliation string.
def extract_departments(affiliation_str):
    segments = affiliation_str.split(";")
    matching_departments = []
    for seg in segments:
        seg_clean = seg.strip()
        # Skip segments that contain any exclusion keyword (case-insensitive)
        if any(excl.lower() in seg_clean.lower() for excl in exclusion_keywords):
            continue
        for dept in valid_departments:
            if dept.lower() in seg_clean.lower():
                if dept not in matching_departments:
                    matching_departments.append(dept)
    if matching_departments:
        return "; ".join(matching_departments)
    else:
        return "Other"

# --- Affiliation Processor Function ---
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

    # Process corresponding author and affiliation extraction.
    df['Corresponding Author'] = ""
    df['Corresponding Affiliation'] = ""
    for index, row in df.iterrows():
        affil_text = row[affil_field]
        parts_list = affil_text.split(";")
        valid_authors = []
        for part in parts_list:
            # Expecting each part to be in the format "Name, Affiliation"
            components = part.strip().split(',', 1)
            if len(components) == 2:
                name, affiliation = components
                affiliation = affiliation.strip()
                # Special handling for Saveetha University
                if "Saveetha University" in affiliation:
                    if "Saveetha University" in valid_affiliations:
                        valid_authors.append((name.strip(), affiliation))
                # Otherwise, check if the affiliation contains any valid affiliation
                elif any(valid in affiliation for valid in valid_affiliations):
                    # Only add if the affiliation does not contain any exclusion keyword
                    if not any(excl.lower() in affiliation.lower() for excl in exclusion_keywords):
                        valid_authors.append((name.strip(), affiliation))
        if valid_authors:
            # Take the last valid author as the corresponding author
            corresponding_author, corresponding_affiliation = valid_authors[-1]
            df.at[index, 'Corresponding Author'] = corresponding_author
            df.at[index, 'Corresponding Affiliation'] = corresponding_affiliation

    # Create the "Department" column using the selected affiliation field.
    df["Department"] = df[affil_field].apply(extract_departments)
    return df

# --- Department Statistics Function ---
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

    # Initialize statistics dictionary for each valid department and "Other".
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
            # Skip segments containing unwanted keywords (case-insensitive)
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

# --- Use st.tabs for functionality selection ---
tabs = st.tabs(["Affiliation Processor", "Department Statistics"])

with tabs[0]:
    st.subheader("Corresponding Author Affiliation Processor")
    if uploaded_file:
        processed_df = process_file(uploaded_file)
        if processed_df is not None:
            st.dataframe(processed_df)
            csv_data = processed_df.to_csv(index=False)
            st.download_button(
                label="Download Updated CSV with Department Column",
                data=csv_data,
                file_name="updated_affiliations.csv",
                mime="text/csv"
            )
    else:
        st.info("Upload a CSV file to start processing for author affiliations.")

with tabs[1]:
    st.subheader("Department Statistics")
    st.write("This module calculates the number of research papers and total citations for each department by matching valid department names (while skipping segments that contain 'College' or 'Affiliated to'). Citation counts are taken from the 'Cited by' column.")
    if uploaded_file:
        stats_df = process_department_stats(uploaded_file)
        if stats_df is not None:
            st.dataframe(stats_df)
            st.markdown("### Papers Published (per Department)")
            st.bar_chart(stats_df.set_index("Department")["Papers"])
            st.markdown("### Total Citations (per Department)")
            st.bar_chart(stats_df.set_index("Department")["Citations"])
            csv_stats = stats_df.to_csv(index=False)
            st.download_button(
                label="Download Department Statistics CSV",
                data=csv_stats,
                file_name="department_statistics.csv",
                mime="text/csv"
            )
    else:
        st.info("Upload a CSV file to calculate department statistics.")

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
