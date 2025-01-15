import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64

# Define the valid affiliations
valid_affiliations = ["Shivaji University", "Saveetha University"]

# Define the exclusion keywords
exclusion_keywords = ["College", "Affiliated to"]

# Streamlit UI
st.title("Research Author Affiliation Processor")
st.write("Upload a CSV file containing authors with affiliations to extract authors from Shivaji University, Kolhapur, and Saveetha University.")

# Container for uploading CSV
with st.container():
    st.subheader("📂 Upload CSV File")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")

# Function to process the CSV file and extract corresponding author and affiliation
def process_file(file):
    df = pd.read_csv(file)

    # Initialize new columns for corresponding author and affiliation
    df['Corresponding Author'] = ""
    df['Corresponding Affiliation'] = ""

    # Process each row in the dataset
    for index, row in df.iterrows():
        authors_with_affiliations = row['Authors with affiliations']  # Ensure this matches your actual column name
        authors_affiliations = authors_with_affiliations.split(';')  # Split authors and affiliations by semicolon

        valid_authors = []  # List to store valid authors with their affiliations
        corresponding_author = None
        corresponding_affiliation = None

        # Process each author-affiliation pair
        for author_affiliation in authors_affiliations:
            parts = author_affiliation.strip().split(',', 1)  # Split name and affiliation
            if len(parts) == 2:
                name, affiliation = parts
                affiliation = affiliation.strip()  # Clean up the affiliation

                # Handle Saveetha University (ignore exclusion keywords)
                if "Saveetha University" in affiliation:
                    if "Saveetha University" in valid_affiliations:
                        valid_authors.append((name.strip(), affiliation))
                # Handle other affiliations (consider exclusion keywords)
                elif any(valid_affiliation in affiliation for valid_affiliation in valid_affiliations):
                    if not any(exclusion in affiliation for exclusion in exclusion_keywords):
                        valid_authors.append((name.strip(), affiliation))

        # If valid authors are found, consider the last one as the corresponding author
        if valid_authors:
            corresponding_author, corresponding_affiliation = valid_authors[-1]
            df.at[index, 'Corresponding Author'] = corresponding_author
            df.at[index, 'Corresponding Affiliation'] = corresponding_affiliation

    return df

# Container for processing file
with st.container():
    if uploaded_file:
        st.write("Processing the uploaded file...")
        processed_df = process_file(uploaded_file)
        st.write("Processed Data:")
        st.dataframe(processed_df)  # Display the updated dataframe

        # Button to download the updated CSV
        st.subheader("📥 Download Processed File")
        csv = processed_df.to_csv(index=False)
        st.download_button(
            label="Download Updated CSV",
            data=csv,
            file_name="updated_affiliations.csv",
            mime="text/csv"
        )
    else:
        st.info("Upload a CSV file to start processing.")

# Info section about the creator
st.info("Created by Dr. Satyajeet Patil")
st.info("For more cool apps like this visit: https://patilsatyajeet.wixsite.com/home/python")

# Support section in an expandable container
with st.expander("🤝 Support Our Research", expanded=False):
    st.markdown(""" 
        <div style='text-align: center; padding: 1rem; background-color: #f0f2f6; border-radius: 10px; margin: 1rem 0;'>
            <h3>🙏 Your Support Makes a Difference!</h3>
            <p>Your contribution helps us continue developing free tools for the research community.</p>
            <p>Every donation, no matter how small, fuels our research journey!</p>
        </div>
        """, unsafe_allow_html=True)

    # Two columns for QR code and Buy Me a Coffee button
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### UPI Payment")
        # Generate UPI QR code
        def generate_qr_code(data):
            qr = qrcode.make(data)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer

        upi_url = "upi://pay?pa=satyajeet1396@oksbi&pn=Satyajeet Patil&cu=INR"
        buffer = generate_qr_code(upi_url)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Display QR code
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
        # Buy Me a Coffee button
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
