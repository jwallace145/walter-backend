import json
from dataclasses import dataclass

from mypy_boto3_bedrock import BedrockClient
from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterBedrockClient:
    """
    Walter Bedrock Client

    This class is a wrapper around the Boto3 Bedrock client and is responsible
    for submitting prompts and returning responses from a foundation model in
    single or batch calls.

    Model IDs: https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html
    """

    bedrock: BedrockClient
    bedrock_runtime: BedrockRuntimeClient

    def __post_init__(self) -> None:
        log.debug(
            f"Creating Bedrock client in region '{self.bedrock.meta.region_name}'"
        )

    def generate_response(self, model_id: str, body: str) -> str:
        """
        Invoke the model and get a response for a single prompt.

        Args:
            model_id: The foundation model to invoke.
            body: The body of inference parameters and prompt to invoke the model.

        Returns:
            The generated response from the given model.
        """
        try:
            log.info(f"Generating response with model '{model_id}'")
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=body,
            )
            model_response = json.loads(response["body"].read())
            return model_response["generation"]
        except Exception as exception:
            log.error(
                "Unexpected error occurred attempting to generate response for prompt!",
                exception,
            )
