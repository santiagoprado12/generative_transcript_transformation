import unittest

from src.generator.file_reader.txt_reader import TXTReader


class TestTXTReader(unittest.TestCase):
    def test_verify_extension_valid(self):
        reader = TXTReader("tests/generator/file_reader/example.txt")
        self.assertTrue(reader.verify_extension())

    def test_verify_extension_invalid(self):
        with self.assertRaises(ValueError):
            TXTReader("example.pdf")

    def test_read_file(self):
        with open("test.txt", "w", encoding="utf-8") as file:
            file.write("Hello, world!")
        reader = TXTReader("test.txt")
        self.assertEqual(reader.read_file(), "Hello, world!")

    def test_process_content(self):
        reader = TXTReader("tests/generator/file_reader/example.txt")
        self.assertEqual(reader.read_file(), "Sample content")

    def test_init_with_valid_file(self):
        with open("test.txt", "w", encoding="utf-8") as file:
            file.write("Hello, world!")
        reader = TXTReader("test.txt")
        self.assertEqual(reader.content, "Hello, world!")

    def test_init_with_invalid_file(self):
        with self.assertRaises(ValueError):
            TXTReader("tests/generator/file_reader/example.invtxt")


if __name__ == "__main__":
    unittest.main()