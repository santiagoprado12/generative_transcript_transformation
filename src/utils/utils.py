import markdown
from weasyprint import HTML
from typing import Dict, Any, List

import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = "".join(page.get_text() for page in doc)
    return text.strip()

def convert_markdown_to_pdf(markdown_content: str, output_path: str) -> None:
    """Convert Markdown content to a PDF file."""
    html_content = markdown.markdown(markdown_content)
    HTML(string=html_content).write_pdf(output_path)

def calculate_word_counts(content_table: Dict[str, Any], required_words: int) -> Dict[str, int]:
    """Calculate word counts for each chapter based on their importance."""
    word_counts = {
        chapter: int(required_words * perc) for chapter, perc in content_table.items()
    }
    return word_counts

def should_refine_chapters(chapters: Dict[str, str], word_counts: Dict[str, int]) -> List[str]:
    """Determine which chapters need refinement based on word counts."""
    chapters_to_refine = [
        chapter for chapter, content in chapters.items()
        if len(content.split()) < word_counts[chapter] * 0.9
    ]
    return chapters_to_refine