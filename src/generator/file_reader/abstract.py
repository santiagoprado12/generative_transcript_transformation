from abc import ABC, abstractmethod


class FileReader(ABC):
    """Abstract base class for reading and processing files.

    This class provides a template for reading files of various types.
    It includes methods to verify the file extension, read the file,
    process the file content, and store the processed content for later use.
    """

    def __init__(self, file_path: str):
        """Initialize the FileReader with the path to the file.

        Args:
            file_path (str): The path to the file to be read.
        """
        self.file_path = file_path
        self.content = None

    @abstractmethod
    def verify_extension(self) -> bool:
        """Verify if the file extension is supported.

        Returns:
            bool: True if the file extension is supported, False otherwise.
        """
        pass

    @abstractmethod
    def read_file(self) -> str:
        """Read the content of the file.

        Returns:
            str: The content of the file as a string.
        """
        pass

    @abstractmethod
    def process_content(self, content: str) -> str:
        """Process the content of the file if needed.

        Args:
            content (str): The content of the file to be processed.

        Returns:
            str: The processed content.
        """
        pass

    def get_content(self) -> str:
        """Get the processed content of the file.

        Returns:
            str: The processed content of the file.
        """
        return self.content


