import json
from dataclasses import dataclass

from src.ai.common.model import WalterFoundationModel
from src.aws.bedrock.client import WalterBedrockClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class MetaLlama38B(WalterFoundationModel):
    """
    Meta Llama 3
    """

    MODEL_NAME = "Meta: Llama3.3 70B"
    MODEL_ID = "arn:aws:bedrock:us-east-1:010526272437:inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
    MAX_INPUT_TOKENS = 128_000

    def __init__(
        self, client: WalterBedrockClient, temperature: float = 0.5, top_p: float = 0.9
    ) -> None:
        super().__init__(
            client,
            MetaLlama38B.MODEL_NAME,
            MetaLlama38B.MODEL_ID,
            MetaLlama38B.MAX_INPUT_TOKENS,
            temperature,
            top_p,
        )

    def _get_body(self, prompt: str, max_output_tokens: int) -> str:
        return json.dumps(
            {
                "prompt": prompt,
                "max_gen_len": max_output_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }
        )

    def _parse_response(self, response: dict) -> str:
        print(response)
        input()
        return response["content"][0]["text"]
