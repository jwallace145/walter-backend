import json
from dataclasses import dataclass

from src.ai.common.model import WalterFoundationModel
from src.aws.bedrock.client import WalterBedrockClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Claude3Haiku(WalterFoundationModel):
    """
    Claude 3.5 Haiku

    Anthropic's fastest, most-compact model for near-instant responsiveness
    with a large context window (200k tokens). The quick response generation
    paired with the large context window allows this model to parse more stock
    market data in a single prompt and generate responses with more proprietary
    data than many other models.

    Link: https://www.anthropic.com/news/claude-3-haiku
    Docs: https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-runtime_example_bedrock-runtime_InvokeModel_AnthropicClaude_section.html
    """

    MODEL_NAME = "Anthropic: Claude 3.5 Haiku"
    MODEL_ID = "arn:aws:bedrock:us-east-1:010526272437:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0"
    MAX_INPUT_TOKENS = 200_000

    def __init__(
        self, client: WalterBedrockClient, temperature: float = 0.5, top_p: float = 0.9
    ) -> None:
        super().__init__(
            client,
            Claude3Haiku.MODEL_NAME,
            Claude3Haiku.MODEL_ID,
            Claude3Haiku.MAX_INPUT_TOKENS,
            temperature,
            top_p,
        )

    def _get_body(self, prompt: str, max_output_tokens: int) -> str:
        native_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_output_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }
        return json.dumps(native_request)

    def _parse_response(self, response: dict) -> str:
        return response["content"][0]["text"]
