from src.templates.engine import TemplatesEngine

TEMPLATE_NAME = "default"


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
