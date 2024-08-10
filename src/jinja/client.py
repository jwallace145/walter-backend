from dataclasses import dataclass
from typing import Dict, List

import yaml
from jinja2 import BaseLoader, Environment
from src.jinja.models import Parameter, Response
from src.s3.client import S3Client
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class TemplateEngine:
    """
    Template Engine

    This class is utilized to create parameterized templates with Jinja.
    The responses from Bedrock are fed into this class to be used in the
    template to create the newsletter.
    """

    OUTPUT_FILE = "tmp/index.html"
    DEFAULT_TEMPLATE = "default"

    s3_client: S3Client

    def __post_init__(self) -> None:
        log.debug("Creating TemplateGenerator client")

    def get_template_spec(
        self, template_name: str = DEFAULT_TEMPLATE
    ) -> List[Parameter]:
        log.info(f"Getting template spec for template: '{template_name}'")
        parameters = []
        for parameter in yaml.safe_load(self.s3_client.get_template_spec())[
            "TemplateSpec"
        ]["Parameters"]:
            parameters.append(Parameter(parameter["Key"], parameter["Prompt"]))
        return parameters

    def render_template(
        self, template_name: str = DEFAULT_TEMPLATE, responses: List[Response] = []
    ) -> None:
        log.info(f"Rendering template: '{template_name}'")
        template = self.s3_client.get_template(template_name)
        environment = Environment(loader=BaseLoader).from_string(template)
        rendered_template = environment.render(
            **TemplateEngine._convert_responses_to_dict(responses)
        )
        self.s3_client.put_newsletter(template_name, rendered_template)
        log.info(f"Finished rendering template: '{template_name}'")

    @staticmethod
    def _convert_responses_to_dict(responses: List[Response]) -> Dict[str, str]:
        responses_dict = {}
        for response in responses:
            responses_dict[response.key] = response.response
        return responses_dict
