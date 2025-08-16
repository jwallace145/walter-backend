from dataclasses import dataclass

import yaml
from jinja2 import BaseLoader, Environment

from src.templates.bucket import TemplatesBucket
from src.templates.models import TemplateSpec, template_spec_from_dict
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class TemplatesEngine:
    """
    Templates Engine
    """

    templates_bucket: TemplatesBucket

    def get_template_spec(
        self, template_name: str, template_spec_args: dict
    ) -> TemplateSpec:
        log.info(f"Rendering template spec for '{template_name}' template")
        log.debug(f"Using template spec args:\n{template_spec_args}")
        template_spec = self.templates_bucket.get_template_spec(template_name)
        rendered_template_spec = (
            Environment(loader=BaseLoader)
            .from_string(template_spec)
            .render(**template_spec_args)
        )
        spec = template_spec_from_dict(yaml.safe_load(rendered_template_spec))
        log.info(f"Finished rendering template spec for '{template_name}' template")
        return spec

    def get_template(
        self,
        template_name: str,
        template_args: dict,
    ) -> str:
        """
        Render and return the given template with the template arguments injected.

        Args:
            template_name: The name of the template to render.
            template_args: The dictionary of template arguments to inject into the template.

        Returns:
            The rendered template as a string.
        """
        log.info(
            f"Rendering '{template_name}' template with {len(template_args)} arguments"
        )
        template = self.templates_bucket.get_template(template_name)
        rendered_template = (
            Environment(loader=BaseLoader)
            .from_string(template.contents)
            .render(**template_args)
        )
        log.info(f"Finished rendering '{template_name}' template")
        return rendered_template
