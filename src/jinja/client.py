from dataclasses import dataclass
from typing import Dict, List

import yaml
from jinja2 import BaseLoader, Environment
from src.environment import Domain
from src.jinja.models import Parameter, Response
from src.s3.client import S3Client
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class TemplateEngine:
    """
    Template Engine

    This class is utilized to render parameterized templates with Jinja.
    The generative AI responses from BedRock are fed into this class
    along with the parameterized template to render the specific email.
    """

    DEFAULT_TEMPLATE = "default"  # TODO: Create mechanism to pull template to use from somewhere... DDB?

    s3_client: S3Client
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(f"Creating '{self.domain.value}' TemplateEngine client")

    def get_template_spec(
        self, template_name: str = DEFAULT_TEMPLATE
    ) -> List[Parameter]:
        """Get template specifications for the given template.

        This method gets the `templatespec.yml` file for the given template from S3.
        The template spec file includes the keys and prompts to use to get AI responses
        from BedRock and where to inject them into the template.

        Args:
            template_name (str, optional): The name of the template to utilize. Default `default`.

        Returns:
            List[Parameter]: The list of parameters included in the template specifications.
                             Each parameter is a tuple of key and prompt where the key represents
                             where to inject the response to the prompt in the template.
        """
        log.info(f"Getting template spec for template: '{template_name}'")
        parameters = []
        for parameter in yaml.safe_load(self.s3_client.get_template_spec())[
            "TemplateSpec"
        ]["Parameters"]:
            parameters.append(Parameter(parameter["Key"], parameter["Prompt"]))
        return parameters

    def get_template_images(self, template_name: str = DEFAULT_TEMPLATE) -> List[str]:
        """Download template images.

        This method downloads the images used by a template from S3 to be packaged and
        sent with the email.

        Args:
            template_name (str, optional): The name of the template to get the images from S3.

        Returns:
            List[str]: The list of paths to the downloaded images from S3.
        """
        log.info(f"Getting images for template: '{template_name}'")
        return self.s3_client.get_template_images()

    def render_template(
        self, template_name: str = DEFAULT_TEMPLATE, responses: List[Response] = []
    ) -> str:
        """Render the template with the AI responses.

        This method renders the given template with the responses from BedRock.

        Args:
            template_name (str, optional): The name of the template to render.
            responses (List[Response], optional): The list of AI responses from BedRock.

        Returns:
            str: The rendered template with AI responses as a string.
        """
        log.info(
            f"Rendering template with {len(responses)} responses: '{template_name}'"
        )
        rendered_template = (
            Environment(loader=BaseLoader)
            .from_string(self.s3_client.get_template(template_name))
            .render(**TemplateEngine._convert_responses_to_dict(responses))
        )
        self.s3_client.put_newsletter(template_name, rendered_template)
        log.info(f"Finished rendering template: '{template_name}'")
        return rendered_template

    @staticmethod
    def _convert_responses_to_dict(responses: List[Response]) -> Dict[str, str]:
        responses_dict = {}
        for response in responses:
            responses_dict[response.key] = response.response
        return responses_dict
