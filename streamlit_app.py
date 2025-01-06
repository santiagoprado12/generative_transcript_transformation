import asyncio
from pathlib import Path

import streamlit as st

from src.generator.pipeline_manager.pipeline import TranscriptPipeline

st.title("Generative Transcript Transformation")

# Text input for instruction
instruction = st.text_input(
    "Enter your instruction:",
    value="Transcript from a cybersecurity SME discussing risks in cloud systems (friendly tone).",
)

# File uploader for PDF
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
word_count = st.slider(
    "Select the number of words:", min_value=1000, max_value=15000, step=100
)

# Button to start processing
if st.button("Generate Transcript"):
    if uploaded_file is not None and instruction:
        # Save the uploaded file
        pdf_path = Path("uploaded_file.pdf")
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        async def run_pipeline():
            # Display progress bar
            progress_bar = st.progress(0)

            initial_state = {"pdf_path": str(pdf_path), "required_words": word_count, "instruction": instruction}
            pipeline = TranscriptPipeline(initial_state)
            pipeline_app = pipeline.app
            steps_completed = tuple()
            total_steps = 5

            async for step in pipeline_app.astream(initial_state):
                steps_completed += (list(step.keys())[0],)
                progress_bar.progress(min((len(steps_completed) / total_steps), 1))

        # Run the pipeline
        asyncio.run(run_pipeline())

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