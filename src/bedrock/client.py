import json
from dataclasses import dataclass
from typing import List

from mypy_boto3_bedrock import BedrockClient
from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
from src.s3.templates.models import Parameter
from src.utils.log import Logger

log = Logger(__name__).get_logger()

PROMPT_FORMAT = """
<|begin_of_text|>
<|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
"""


@dataclass
class BedrockClient:
    """
    Bedrock Client
    """

    META_LLAMA3_8B_MODEL_ID = "meta.llama3-70b-instruct-v1:0"

    bedrock: BedrockClient
    bedrock_runtime: BedrockRuntimeClient

    def __post_init__(self) -> None:
        log.debug(
            f"Creating Bedrock client in region '{self.bedrock.meta.region_name}'"
        )

    def generate_responses(self, parameters: List[Parameter]) -> List[Parameter]:
        log.info(f"Generating AI response for {len(parameters)} prompts")
        responses = []
        for parameter in parameters:
            responses.append(
                Parameter(parameter.key, self.generate_response(parameter.prompt))
            )
        return responses

    def generate_response(self, prompt: str) -> str:
        try:
            log.info(
                f"Generating response with model {BedrockClient.META_LLAMA3_8B_MODEL_ID}:\n{prompt}"
            )
            response = self.bedrock_runtime.invoke_model(
                modelId=BedrockClient.META_LLAMA3_8B_MODEL_ID,
                body=BedrockClient._get_request(prompt),
            )
            model_response = json.loads(response["body"].read())
            return model_response["generation"]
        except Exception as exception:
            log.error(
                "Unexpected error occurred attempting to generate response for prompt!",
                exception,
            )
            exit(1)

    @staticmethod
    def _get_request(prompt: str) -> str:
        return json.dumps(
            {
                "prompt": PROMPT_FORMAT.format(prompt=prompt),
                "max_gen_len": 512,
                "temperature": 0.5,
            }
        )
