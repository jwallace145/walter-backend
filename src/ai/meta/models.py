import json
from dataclasses import dataclass
from typing import List

from src.ai.client import WalterBedrockClient
from src.ai.models import Prompt, Response
from src.utils.log import Logger

log = Logger(__name__).get_logger()

PROMPT_FORMAT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are the author of a business casual newsletter that helps users with their stock portfolios<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
"""(str): The prompt format for Meta Llama3 models. For more information, see: https://www.llama.com/docs/model-cards-and-prompt-formats/meta-llama-3/ """


@dataclass
class MetaLlama38B:

    MODEL_ID = "meta.llama3-70b-instruct-v1:0"

    model: WalterBedrockClient

    temperature: float = 0.5
    top_p: float = 0.9

    def generate_responses(self, prompts: List[Prompt]) -> List[Response]:
        """
        Invoke the foundation model and get responses for the list of prompts given.

        This method makes a single API call to Bedrock for each prompt included in the
        list of prompts.

        Args:
            prompts: The list of prompts to invoke the foundation model.

        Returns:
            The responses to the list of prompts.
        """
        log.info(f"Generating responses for {len(prompts)} prompts")
        return [
            Response(
                prompt.name,
                self.model.generate_response(
                    MetaLlama38B.MODEL_ID, self._get_body(prompt)
                ),
            )
            for prompt in prompts
        ]

    def _get_body(self, prompt: Prompt) -> str:
        return json.dumps(
            {
                "prompt": PROMPT_FORMAT.format(prompt=prompt.prompt),
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_gen_len": prompt.max_gen_len,
            }
        )
