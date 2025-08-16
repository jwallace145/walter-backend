from enum import Enum
from typing import Dict, List

from src.ai.amazon.models import NovaLite, NovaMicro
from src.ai.anthropic.models import Claude3Haiku, Claude3SonnetV2
from src.ai.meta.models import Llama370B


class WalterModel(Enum):
    """
    Models

    This enum represents the Bedrock models supported by Walter.
    To switch between models for AI response generation, specify
    the desired model name in the config.yml file.
    """

    AMAZON_NOVA_MICRO: str = NovaMicro.MODEL_NAME
    AMAZON_NOVA_LITE: str = NovaLite.MODEL_NAME
    ANTHROPIC_CLAUDE_3_HAIKU: str = Claude3Haiku.MODEL_NAME
    ANTHROPIC_CLAUDE_3_SONNET_V2: str = Claude3SonnetV2.MODEL_NAME
    META_LLAMA3_70B: str = Llama370B.MODEL_NAME


SUPPORTED_MODEL_NAME_TO_WALTER_MODEL: Dict[str, WalterModel] = {
    model.value: model for model in WalterModel
}
"""(Dict[str, WalterModel]: The model names supported by Walter to Walter model enum member."""

SUPPORTED_WALTER_MODEL_NAMES: List[str] = [model.value for model in WalterModel]
"""(List[str]: The model names supported by Walter."""

SUPPORTED_WALTER_MODELS: List[WalterModel] = [model for model in WalterModel]
"""(List[WalterModel]): The models supported by Walter."""
