import unittest
from abc import ABC, abstractmethod

from src.generator.file_reader.abstract import FileReader


class TestFileReader(FileReader):
    """Concrete implementation of FileReader for testing purposes."""

    def verify_extension(self) -> bool:
        return self.file_path.endswith('.txt')

    def read_file(self) -> str:
        return "dummy content"

    def process_content(self, content: str) -> str:
        return content.upper()

class TestFileReaderAbstract(unittest.TestCase):
    def setUp(self):
        self.file_reader = TestFileReader("test.txt")

    def test_verify_extension(self):
        self.assertTrue(self.file_reader.verify_extension())

    def test_read_file(self):
        content = self.file_reader.read_file()
        self.assertEqual(content, "dummy content")

    def test_process_content(self):
        processed_content = self.file_reader.process_content("dummy content")
        self.assertEqual(processed_content, "DUMMY CONTENT")

    def test_get_content(self):
        self.file_reader.content = "processed content"
        self.assertEqual(self.file_reader.get_content(), "processed content")

if __name__ == '__main__':
    unittest.main()