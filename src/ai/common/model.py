import json
from abc import ABC, abstractmethod

from src.aws.bedrock.client import WalterBedrockClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class WalterFoundationModel(ABC):
    """
    WalterAI - Foundation Model Base Class

    This class contains the core, undifferentiated logic to generate a response
    given a Bedrock model and a prompt.
    """

    def __init__(
        self,
        client: WalterBedrockClient,
        model_name: str,
        model_id: str,
        max_input_tokens: int,
        temperature: float = 0.5,
        top_p: float = 0.9,
    ) -> None:
        self.client = client
        self.model_name = model_name
        self.model_id = model_id
        self.max_input_tokens = max_input_tokens
        self.temperature = temperature
        self.top_p = top_p

    def generate_response(self, prompt: str, max_output_tokens: int) -> str:
        """
        Generate a response given a prompt and max number of tokens.

        Args:
            prompt (str): The given prompt.
            max_output_tokens (int): The maximum number of tokens to include in the output.

        Returns:
            (str): The generated response.
        """
        log.info(
            f"Invoking model '{self.model_name}' and generating a response with max output tokens: {max_output_tokens}"
        )
        self._verify_prompt(prompt)
        body = self._get_body(prompt, max_output_tokens)
        log.debug(f"Prompt body:\n{json.dumps(body, indent=4)}")
        response = self.client.generate_response(self.model_id, body)
        parsed_response = self._parse_response(response)
        log.debug(f"Response:\n{parsed_response}")
        log.info("Successfully returned a response!")
        return parsed_response

    def _verify_prompt(self, prompt: str) -> None:
        """
        This method verifies that the input prompt is valid.

        The main requirement to verify is that the prompt size is less than the
        max input tokens allowed for the given model. Some models have relatively
        small context windows which Walter can break if it is including too much
        data in the prompt.

        Args:
            prompt: The prompt to verify.
        """
        log.debug("Verifying prompt...")
        if len(prompt) > self.max_input_tokens:
            raise ValueError("Prompt too long!")

    @abstractmethod
    def _get_body(self, prompt: str, max_output_tokens: int) -> dict:
        pass

    @abstractmethod
    def _parse_response(self, response: dict) -> str:
        pass
