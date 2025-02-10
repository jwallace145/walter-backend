from dataclasses import dataclass
from enum import Enum

from src.ai.amazon.models import NovaMicro
from src.ai.anthropic.models import Claude3Haiku
from src.ai.meta.models import MetaLlama38B


class Model(Enum):
    META_LLAMA3_70B = MetaLlama38B.MODEL_NAME
    ANTHROPIC_CLAUDE_3_HAIKU = Claude3Haiku.MODEL_NAME
    AMAZON_NOVA_MICRO = NovaMicro.MODEL_NAME


def get_model(model_name: str) -> Model:
    for model in Model:
        if model.value == model_name:
            return model
    raise ValueError(
        f"Unexpected model '{model_name}' given! Acceptable models: {[model.value for model in Model]}"
    )


@dataclass
class Prompt:
    name: str
    prompt: str
    max_gen_len: float


@dataclass
class Response:
    name: str
    response: str
