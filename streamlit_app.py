import streamlit as st
import asyncio
from pathlib import Path

from test import app  # Assuming the previous code is in a file named test.py

st.title("Generative Transcript Transformation")

# Text input for instruction
instruction = st.text_input("Enter your instruction:")

# File uploader for PDF
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# Button to start processing
if st.button("Generate Transcript"):
    if uploaded_file is not None and instruction:
        # Save the uploaded file
        pdf_path = Path("uploaded_file.pdf")
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Display progress bar
        progress_bar = st.progress(0)

        async def run_app():
            initial_state = {"pdf_path": str(pdf_path)}
            await app.ainvoke(initial_state)
            progress_bar.progress(100)

        # Run the app
        asyncio.run(run_app())

        # Display the generated PDF
        st.success("Transcript generated successfully!")
        with open("output_file.pdf", "rb") as f:
            st.download_button(
                label="Download Transcript",
                data=f,
                file_name="output_file.pdf",
                mime="application/pdf",
            )
    else:
        st.error("Please provide an instruction and upload a PDF file.")