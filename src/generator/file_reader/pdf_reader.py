import PyPDF2
from src.generator.file_reader.abstract import FileReader


class PDFReader(FileReader):
    """Concrete implementation of FileReader for PDF files."""

    def verify_extension(self) -> bool:
        """Verify if the file extension is .pdf.

        Returns:
            bool: True if the file extension is .pdf, False otherwise.
        """
        return self.file_path.lower().endswith('.pdf')

    def read_file(self) -> str:
        """Read the content of the PDF file.

        Returns:
            str: The content of the PDF file as a string.
        """
        content = ""
        with open(self.file_path, 'rb') as file:
            reader = PyPDF2.PdfFileReader(file)
            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                content += page.extract_text()
        return content

    def process_content(self, content: str) -> str:
        """Process the content of the PDF file if needed.

        Args:
            content (str): The content of the PDF file to be processed.

        Returns:
            str: The processed content.
        """
        # For this example, we'll just return the content as is.
        return content

    def __init__(self, file_path: str):
        super().__init__(file_path)
        if self.verify_extension():
            raw_content = self.read_file()
            self.content = self.process_content(raw_content)
        else:
            raise ValueError("Unsupported file extension. Only .pdf files are supported.")