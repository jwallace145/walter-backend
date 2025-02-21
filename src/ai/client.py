from dataclasses import dataclass

from src.ai.amazon.models import NovaMicro, NovaLite
from src.ai.anthropic.models import Claude3Haiku, Claude3SonnetV2
from src.ai.common.model import WalterFoundationModel
from src.ai.exceptions import UnknownModel
from src.ai.meta.models import Llama370B
from src.ai.models import (
    WalterModel,
    SUPPORTED_MODEL_NAME_TO_WALTER_MODEL,
    SUPPORTED_WALTER_MODEL_NAMES,
    SUPPORTED_WALTER_MODELS,
)
from src.aws.bedrock.client import WalterBedrockClient
from src.config import CONFIG
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterAI:
    """
    WalterAI

    The AI orchestration class that is responsible for generating
    responses for given prompts with the desired and supported
    models.
    """

    model_name: str
    client: WalterBedrockClient

    model: WalterFoundationModel = None  # set during post-init

    def __post_init__(self) -> None:
        log.debug(f"Creating WalterAI with model '{self.model_name}'...")
        self.model = self._get_model()

    def generate_response(self, prompt: str, max_output_tokens: int) -> str:
        """
        Generate a response from the given prompt.

        This method generates a response for the given prompt with the
        desired model.

        Args:
            prompt (str): The prompt to feed into the selected model.
            max_output_tokens (int): The maximum number of output tokens included
            in the response

        Returns:
            (str): The generated response for the prompt.
        """
        return self.model.generate_response(
            prompt=prompt, max_output_tokens=max_output_tokens
        )

    def _get_model(self) -> WalterFoundationModel:
        """
        Get the WalterFoundationModel given the model name.

        The WalterFoundationModel is the instantiated model that can be
        used to generate AI responses. WalterAI orchestrates passing in
        common WalterFoundationModel configs such as the temperature and
        top p of the model and selecting the right model given the model
        name.

        Returns:
            (WalterFoundationModel): The instantiated WalterFoundationModel.
        """
        model = WalterAI.get_model(self.model_name)
        if model == WalterModel.AMAZON_NOVA_MICRO:
            return NovaMicro(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
        elif model == WalterModel.AMAZON_NOVA_LITE:
            return NovaLite(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
        elif model == WalterModel.ANTHROPIC_CLAUDE_3_HAIKU:
            return Claude3Haiku(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
        elif model == WalterModel.ANTHROPIC_CLAUDE_3_SONNET_V2:
            return Claude3SonnetV2(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
        elif model == WalterModel.META_LLAMA3_70B:
            return Llama370B(
                client=self.client,
                temperature=CONFIG.artificial_intelligence.temperature,
                top_p=CONFIG.artificial_intelligence.top_p,
            )
        else:
            raise UnknownModel(
                f"Unknown model '{model}'! Acceptable models: {SUPPORTED_WALTER_MODELS}"
            )

    @staticmethod
    def get_model(model_name: str) -> WalterModel:
        """
        Get model from WalterModel enum by model name.

        This method throws an UnknownModel exception if given model name
        is not found in the WalterModel enum.

        Args:
            model_name (str): The model name.

        Returns:
            (WalterModel): The corresponding WalterModel enum.
        """
        if model_name in SUPPORTED_MODEL_NAME_TO_WALTER_MODEL:
            return SUPPORTED_MODEL_NAME_TO_WALTER_MODEL[model_name]
        raise UnknownModel(
            f"Unexpected model '{model_name}' given! Acceptable models: {SUPPORTED_WALTER_MODEL_NAMES}"
        )
