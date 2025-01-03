import openai
from abstract import GenAIModelManager

class OpenAIModelManager(GenAIModelManager):
    """A class to manage OpenAI models like GPT-3.

    This class extends GenAIModelManager to manage OpenAI models.
    It includes functionality to generate text based on a given prompt using OpenAI's API.

    Methods:
        generate_text(self, prompt: str) -> str: Generates text based on the given prompt using OpenAI's API.
    """
    def __init__(self, model_name: str = "davinci-codex", max_tokens:int = 150):
        """Initializes the OpenAIModelManager with the specified model name.

        Args:
            model_name (str): The name of the generative AI model being used. Defaults to "openai".
        """
        super().__init__(model_name)

    def generate_text(self, prompt: str) -> str:
        """Generates text based on the given prompt using OpenAI's API.

        Args:
            prompt (str): The prompt to generate text from.

        Returns:
            str: The generated text.
        """
        response = openai.Completion.create(
            engine=self.model_name,
            prompt=prompt,
            max_tokens=self.max_tokens,
            api_key=self.api_key
        )
        return response.choices[0].text.strip()