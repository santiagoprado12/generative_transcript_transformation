import unittest
from unittest.mock import MagicMock, mock_open, patch

from src.generator.file_reader.pdf_reader import PDFReader


class TestPDFReader(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data=b"dummy data")
    @patch("PyPDF2.PdfFileReader")
    def test_verify_extension(self, mock_pdf_reader, mock_file):
        reader = PDFReader("dummy.pdf")
        self.assertTrue(reader.verify_extension())

    @patch("builtins.open", new_callable=mock_open, read_data=b"dummy data")
    @patch("PyPDF2.PdfFileReader")
    def test_read_file(self, mock_pdf_reader, mock_file):
        mock_pdf = MagicMock()
        mock_pdf.numPages = 1
        mock_pdf.getPage.return_value.extract_text.return_value = "Page content"
        mock_pdf_reader.return_value = mock_pdf

        reader = PDFReader("dummy.pdf")
        content = reader.read_file()
        self.assertEqual(content, "Page content")

    @patch("builtins.open", new_callable=mock_open, read_data=b"dummy data")
    @patch("PyPDF2.PdfFileReader")
    def test_process_content(self, mock_pdf_reader, mock_file):
        reader = PDFReader("dummy.pdf")
        processed_content = reader.process_content("Some content")
        self.assertEqual(processed_content, "Some content")

    def test_init_with_valid_extension(self):
        with patch.object(PDFReader, 'read_file', return_value="Raw content"):
            with patch.object(PDFReader, 'process_content', return_value="Processed content"):
                reader = PDFReader("dummy.pdf")
                self.assertEqual(reader.content, "Processed content")

    def test_init_with_invalid_extension(self):
        with self.assertRaises(ValueError):
            PDFReader("dummy.txt")

if __name__ == "__main__":
    unittest.main()