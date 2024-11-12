from dataclasses import dataclass

from src.ai.meta.models import MetaLlama38B
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

    def generate_response(self, context: str, prompt: str, max_gen_len: int) -> str:
        return self._get_model().generate_response(context, prompt, max_gen_len)

    def _get_model(self) -> MetaLlama38B:
        model = get_model(self.model)
        log.info(f"Getting model: '{model.name}'")

        # TODO: Fix this mapping from Llama3 70B to Llama3 8B
        if model == Model.META_LLAMA3_70B:
            return MetaLlama38B(
                client=self.client, temperature=CONFIG.temperature, top_p=CONFIG.top_p
            )
