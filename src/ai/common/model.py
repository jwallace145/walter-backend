from abc import ABC, abstractmethod

from src.aws.bedrock.client import WalterBedrockClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class WalterFoundationModel(ABC):

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
        log.info(
            f"Invoking model '{self.get_name()}' and generating a response with max output tokens: {max_output_tokens}"
        )
        self._verify_prompt(prompt)
        body = self._get_body(prompt, max_output_tokens)
        log.debug(f"Prompt body:\n{body}")
        response = self.client.generate_response(self.model_id, body)
        response = self._parse_response(response)
        log.debug(f"Response:\n{response}")
        log.info("Successfully returned a response!")
        return response

    def get_name(self) -> str:
        return self.model_name

    def _verify_prompt(self, prompt: str) -> None:
        log.debug("Verifying prompt...")
        if len(prompt) > self.max_input_tokens:
            raise ValueError("Prompt too long!")

    @abstractmethod
    def _get_body(self, prompt: str, max_output_tokens: int) -> str:
        pass

    @abstractmethod
    def _parse_response(self, response: dict) -> str:
        pass
