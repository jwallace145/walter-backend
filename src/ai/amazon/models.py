from dataclasses import dataclass

from src.ai.common.model import WalterFoundationModel
from src.aws.bedrock.client import WalterBedrockClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class NovaLite(WalterFoundationModel):
    """
    Amazon Nova Lite
    """

    MODEL_NAME = "Amazon: Nova Lite"
    MODEL_ID = "amazon.nova-lite-v1:0"
    MAX_INPUT_TOKENS = 300_000

    def __init__(
        self, client: WalterBedrockClient, temperature: float = 0.5, top_p: float = 0.9
    ) -> None:
        super().__init__(
            client,
            NovaLite.MODEL_NAME,
            NovaLite.MODEL_ID,
            NovaLite.MAX_INPUT_TOKENS,
            temperature,
            top_p,
        )

    def _get_body(self, prompt: str, max_output_tokens: int) -> dict:
        return {
            "inferenceConfig": {"max_new_tokens": max_output_tokens},
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
        }

    def _parse_response(self, response: dict) -> str:
        return response["output"]["message"]["content"][0]["text"]


@dataclass
class NovaMicro(WalterFoundationModel):
    """
    Amazon Nova Micro
    """

    MODEL_NAME = "Amazon: Nova Micro"
    MODEL_ID = "amazon.nova-micro-v1:0"
    MAX_INPUT_TOKENS = 128_000

    def __init__(
        self, client: WalterBedrockClient, temperature: float = 0.5, top_p: float = 0.9
    ) -> None:
        super().__init__(
            client,
            NovaMicro.MODEL_NAME,
            NovaMicro.MODEL_ID,
            NovaMicro.MAX_INPUT_TOKENS,
            temperature,
            top_p,
        )

    def _get_body(self, prompt: str, max_output_tokens: int) -> dict:
        return {
            "inferenceConfig": {"max_new_tokens": max_output_tokens},
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
        }

    def _parse_response(self, response: dict) -> str:
        return response["output"]["message"]["content"][0]["text"]
