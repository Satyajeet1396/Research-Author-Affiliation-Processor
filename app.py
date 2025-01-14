import streamlit as st
import qrcode
from io import BytesIO
import base64

# Title of the app
st.title("PDF Binder Tool")
st.write("Upload multiple PDF files, and we'll combine their first pages into one PDF for download.")

# File uploader for multiple PDF files
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

# Function to create a PDF binder
def create_pdf_binder(files):
    from PyPDF2 import PdfReader, PdfWriter
    pdf_writer = PdfWriter()
    for uploaded_file in files:
        try:
            pdf_reader = PdfReader(uploaded_file)
            if len(pdf_reader.pages) > 0:  # Updated to check page count
                first_page = pdf_reader.pages[0]
                pdf_writer.add_page(first_page)
        except Exception as e:
            st.warning(f"Could not process file {uploaded_file.name}: {e}")
    return pdf_writer

# Button to create binder
if st.button("Create Binder") and uploaded_files:
    pdf_writer = create_pdf_binder(uploaded_files)
    if pdf_writer.pages:
        # Save the result to an in-memory file
        binder_output = BytesIO()
        pdf_writer.write(binder_output)
        binder_output.seek(0)

        # Create a download button
        st.download_button(
            label="Download Binder PDF",
            data=binder_output,
            file_name="binder.pdf",
            mime="application/pdf"
        )
        st.success("Binder created successfully! Click the button to download.")
    else:
        st.warning("No pages found in the uploaded PDF files.")
else:
    st.info("Upload PDF files and click 'Create Binder' to proceed.")

# Info section about the creator
st.info("Created by Dr. Satyajeet Patil")
st.info("For more cool apps like this visit: https://patilsatyajeet.wixsite.com/home/python")

# Title of the section for QR code
st.title("Support our Research")
st.write("Scan the QR code below to make a payment to: satyajeet1396@oksbi")

# Function to generate the QR code without caching
def generate_qr_code(data):
    if not data:
        st.error("Invalid data for QR Code generation")
        return None
    
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# Sample UPI URL (ensure it's correctly formed)
upi_url = "upi://pay?pa=satyajeet1396@oksbi&pn=Satyajeet Patil&cu=INR"

# Generate QR code
buffer = generate_qr_code(upi_url)

# If QR code was generated successfully, display it
if buffer:
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Center-align the QR code image using HTML and CSS
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; align-items: center;">
            <img src="data:image/png;base64,{qr_base64}" width="200">
        </div>
        """,
        unsafe_allow_html=True
    )

# Display the "Buy Me a Coffee" button as an image link
st.markdown(
    """
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://www.buymeacoffee.com/researcher13" target="_blank">
            <img src="https://img.buymeacoffee.com/button-api/?text=Support our Research&emoji=&slug=researcher13&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff" alt="Support our Research"/>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)

st.info("A small donation from you can fuel our research journey, turning ideas into breakthroughs that can change lives!")
