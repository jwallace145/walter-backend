import pytest

from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine

TEMPLATE_NAME = "default"


@pytest.fixture
def template_engine(templates_bucket: TemplatesBucket) -> None:
    return TemplatesEngine(templates_bucket)


def test_get_template_spec(template_engine: TemplatesEngine) -> None:
    template_spec_args = {
        "user": "walter",
        "datestamp": "2024-12-01T00:00:00Z",
        "portfolio_value": "$100.00",
        "stocks": [],
        "news": [],
    }
    template_engine.get_template_spec(
        template_name=TEMPLATE_NAME, template_spec_args=template_spec_args
    )
