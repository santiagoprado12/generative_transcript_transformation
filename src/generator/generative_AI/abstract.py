import os


class GenAIModelManager:
    """A class to manage generative AI models like ChatGPT or Claude.

    This class is designed to be extended to manage various generative AI models.
    It includes functionality to extract necessary keys from environment variables
    and to generate text based on a given prompt.

    Attributes:
        api_key (str): The API key required to access the generative AI model.
        model_name (str): The name of the generative AI model being used.

    Methods:
        __init__(self, model_name: str): Initializes the GenAIModelManager with the specified model name.
        _load_api_key(self): Loads the API key from environment variables.
        generate_text(self, prompt: str) -> str: Generates text based on the given prompt.
    """
    def __init__(self, model_name: str):
        """Initializes the GenAIModelManager with the specified model name.

        Args:
            model_name (str): The name of the generative AI model being used.
        """
        self.model_name = model_name
        self.api_key = self._load_api_key()

    def _load_api_key(self) -> str:
        """Loads the API key from environment variables.

        Returns:
            str: The API key required to access the generative AI model.
        """
        api_key = os.getenv(f"{self.model_name.upper()}_API_KEY")
        if not api_key:
            raise ValueError(f"API key for {self.model_name} not found in environment variables.")
        return api_key

    def generate_text(self, prompt: str) -> str:
        """Generates text based on the given prompt.

        Args:
            prompt (str): The prompt to generate text from.

        Returns:
            str: The generated text.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")