from dataclasses import dataclass

import yaml
from jinja2 import Environment, BaseLoader

from src.templates.bucket import TemplatesBucket
from src.templates.spec import TemplateSpec, template_spec_from_dict
from src.utils.log import Logger


log = Logger(__name__).get_logger()


@dataclass
class TemplatesEngine:
    """
    Templates Engine
    """

    templates_bucket: TemplatesBucket

    def get_template_spec(
        self,
        template_name: str,
        user: str,
        datestamp: str,
        portfolio_value: str,
        stocks: list,
    ) -> TemplateSpec:
        log.info(f"Rendering template spec for '{template_name}' template")
        template_spec = self.templates_bucket.get_template_spec(template_name)
        rendered_template_spec = (
            Environment(loader=BaseLoader)
            .from_string(template_spec)
            .render(
                user=user,
                datestamp=datestamp,
                portfolio_value=portfolio_value,
                stocks=stocks,
            )
        )
        spec = template_spec_from_dict(yaml.safe_load(rendered_template_spec))
        log.info(f"Finished rendering template spec for '{template_name}' template")
        return spec

    def _render_template(self) -> None:
        log.info("Rendering template...")
