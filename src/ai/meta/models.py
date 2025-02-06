import json
from dataclasses import dataclass

from src.aws.bedrock.client import WalterBedrockClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()

PROMPT_FORMAT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{context}<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
"""(str): The prompt format for Meta Llama3 models. For more information, see: https://www.llama.com/docs/model-cards-and-prompt-formats/meta-llama-3/ """


@dataclass
class MetaLlama38B:
    """
    Meta Llama 3
    """

    MODEL_ID = "meta.llama3-70b-instruct-v1:0"
    MODEL_NAME = "Meta Llama 3"

    client: WalterBedrockClient

    temperature: float = 0.5
    top_p: float = 0.9

    def generate_response(self, context: str, prompt: str, max_gen_len: int) -> str:
        log.info("Invoking model and generating a response...")
        body = self._get_body(context, prompt, max_gen_len)
        log.debug(f"Prompt body:\n{body}")
        response = self.client.generate_response(self.MODEL_ID, body)
        log.debug(f"Response:\n{response}")
        log.info("Successfully returned a response!")
        return response

    def get_name(self) -> str:
        return self.MODEL_NAME

    def _get_body(self, context: str, prompt: str, max_gen_len: int) -> str:
        return json.dumps(
            {
                "prompt": PROMPT_FORMAT.format(context=context, prompt=prompt),
                "temperature": self.temperature,
                "top_p": self.top_p,
                "max_gen_len": max_gen_len,
            },
            indent=4,
        )
