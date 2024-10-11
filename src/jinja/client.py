from dataclasses import dataclass
from typing import Dict, List

from jinja2 import BaseLoader, Environment

from src.ai.models import Response
from src.environment import Domain
from src.newsletters.client import NewslettersBucket
from src.templates.client import TemplatesBucket
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class TemplateEngine:
    """
    Template Engine

    This class is utilized to render parameterized templates with Jinja.
    The generative AI responses from Bedrock are fed into this class
    along with the parameterized template to render the user newsletter.
    """

    DEFAULT_TEMPLATE = "default"  # TODO: Create mechanism to pull template to use from somewhere... DDB?

    templates_bucket: TemplatesBucket
    newsletters_bucket: NewslettersBucket
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(
            f"Creating '{self.domain.value}' TemplateEngine client with templates bucket '{self.templates_bucket.bucket}'"
        )

    def render_template(
        self,
        template_name: str = DEFAULT_TEMPLATE,
        responses: List[Response] = [],
    ) -> str:
        """Render the template with the AI responses.

        This method renders the given template with the responses from BedRock.

        Args:
            template_name (str, optional): The name of the template to render.
            parameters (List[Response], optional): The list of AI responses from Bedrock.

        Returns:
            str: The rendered template with AI responses as a string.
        """
        log.info(
            f"Rendering '{template_name}' template with {len(responses)} responses"
        )
        template = self.templates_bucket.get_template(template_name)
        rendered_template = (
            Environment(loader=BaseLoader)
            .from_string(template.contents)
            .render(**TemplateEngine._convert_responses_to_dict(responses))
        )
        log.info(f"Finished rendering '{template_name}' template")
        return rendered_template

    @staticmethod
    def _convert_responses_to_dict(responses: List[Response]) -> Dict[str, str]:
        responses_dict = {}
        for response in responses:
            print(response)
            responses_dict[response.name] = response.response
        return responses_dict
