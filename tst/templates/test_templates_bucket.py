from src.templates.bucket import TemplatesBucket

TEMPLATE_NAME = "default"


def test_get_template_spec(templates_bucket: TemplatesBucket) -> None:
    templates_bucket.get_template_spec(template=TEMPLATE_NAME)


def test_get_template(templates_bucket: TemplatesBucket) -> None:
    templates_bucket.get_template(template=TEMPLATE_NAME)
