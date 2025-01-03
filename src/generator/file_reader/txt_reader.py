from src.generator.file_reader.abstract import FileReader


class TXTReader(FileReader):
    """Concrete implementation of FileReader for TXT files."""

    def verify_extension(self) -> bool:
        """Verify if the file extension is .txt.

        Returns:
            bool: True if the file extension is .txt, False otherwise.
        """
        return self.file_path.lower().endswith('.txt')

    def read_file(self) -> str:
        """Read the content of the TXT file.

        Returns:
            str: The content of the TXT file as a string.
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def process_content(self, content: str) -> str:
        """Process the content of the TXT file if needed.

        Args:
            content (str): The content of the TXT file to be processed.

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
            raise ValueError("Unsupported file extension. Only .txt files are supported.")