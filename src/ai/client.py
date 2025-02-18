from dataclasses import dataclass

from src.ai.amazon.models import NovaMicro
from src.ai.anthropic.models import Claude3Haiku
from src.ai.common.model import WalterFoundationModel
from src.ai.meta.models import Llama370B
from src.ai.models import get_model, Model
from src.aws.bedrock.client import WalterBedrockClient
from src.config import CONFIG
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterAI:

    model: str
    client: WalterBedrockClient

    def __post_init__(self) -> None:
        log.debug("Creating WalterAI")

    def generate_response(
        self, context: str, prompt: str, max_output_tokens: int
    ) -> str:
        prompt_with_context = f"Context: {context}\nPrompt: {prompt}"
        return self.get_model().generate_response(
            prompt_with_context, max_output_tokens
        )

    def get_model(self) -> WalterFoundationModel:
        model = get_model(self.model)
        log.debug(f"Getting model: '{model.value}'")

        if model == Model.META_LLAMA3_70B:
            return Llama370B(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
        elif model == Model.ANTHROPIC_CLAUDE_3_HAIKU:
            return Claude3Haiku(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
        elif model == Model.AMAZON_NOVA_MICRO:
            return NovaMicro(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
