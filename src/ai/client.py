from dataclasses import dataclass
from typing import List

from src.ai.context.models import Context
from src.ai.meta.models import MetaLlama38B
from src.ai.models import Prompt, Response, get_model, Model
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

    def generate_responses(
        self, context: Context, prompts: List[Prompt]
    ) -> List[Response]:
        return self._get_model().generate_responses(context.context, prompts)

    def _get_model(self) -> MetaLlama38B:
        model = get_model(self.model)
        log.info(f"Getting model: '{model.name}'")

        if model == Model.META_LLAMA3_70B:
            return MetaLlama38B(
                client=self.client, temperature=CONFIG.temperature, top_p=CONFIG.top_p
            )
