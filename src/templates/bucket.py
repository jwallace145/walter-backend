from dataclasses import dataclass

from src.aws.s3.client import WalterS3Client
from src.environment import Domain
from src.templates.models import Template, TemplateAssets
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class TemplatesBucket:
    """
    Templates S3 Bucket
    """

    BUCKET = "walterai-templates-{domain}"

    TEMPLATES_DIR = "templates"
    TEMPLATE_DIR = "{templates_dir}/{template}/"
    ASSETS_DIR = "{templates_dir}/{template}/assets/"

    DEFAULT_TEMPLATE = "default"
    TEMPLATE_SPEC = "templatespec.jinja"
    TEMPLATE = "template.jinja"

    client: WalterS3Client
    domain: Domain

    bucket: str = None  # set during post init

    def __post_init__(self) -> None:
        self.bucket = TemplatesBucket._get_bucket_name(self.domain)
        log.debug(
            f"Creating '{self.domain.value}' TemplatesBucket S3 client with bucket '{self.bucket}'"
        )

    def get_template_spec(self, template: str = DEFAULT_TEMPLATE) -> str:
        """Get template spec YAML config file from S3.

        This method gets the template spec YAML config file from S3 for the given template.
        The template spec file contains the template keys and prompts to use to successfully
        render the template.

        Args:
            template_name (str, optional): The name of the template to get the template spec.

        Returns:
            TemplateSpec: The template spec file.
        """
        log.info(f"Getting '{template}' template spec from S3")
        key = TemplatesBucket._get_template_spec_key(template)
        return self.client.get_object(self.bucket, key)

    def get_template(self, template: str = DEFAULT_TEMPLATE) -> Template:
        """Get Jinja template from S3.

        This method gets the Jinja template from S3 for the given template. The Jinja template
        is utilized to render the user email with the AI responses to the intended prompts.
        Each template in S3 is required to have a Jinja template file.

        Args:
            template_name (str, optional): The name of the template to get the Jinja template.

        Returns:
            str: The Jinja template.
        """
        log.info(f"Getting '{template}' template from S3")
        key = TemplatesBucket._get_template_key(template)
        return Template(
            name=template, contents=self.client.get_object(self.bucket, key)
        )

    def get_template_assets(self, template: str = DEFAULT_TEMPLATE) -> TemplateAssets:
        """Get template assets from S3.

        This method gets the template assets for the given template from S3. The asset(s)
        are included in the generated emails as attachments and referenced by the rendered
        template. Templates that reference external assets must have their assets in S3
        in order to generate the emails successfully.

        Args:
            template_name (str, optional): The name of the template to get assets from S3.

        Returns:
            TemplateAssets: The assets of the given template from S3.
        """
        log.info(f"Getting '{template}' template assets from S3")
        prefix = TemplatesBucket._get_assets_prefix(template)

        # for each key get asset name and download object to memory
        assets = {}
        for key in self.client.list_objects(self.bucket, prefix):
            asset_name = key.split("/")[-1]

            # if asset name is empty skip, weird S3 list behavior
            if asset_name == "":
                continue

            assets[asset_name] = self.client.download_object(self.bucket, key)

        return TemplateAssets(template, assets)

    @staticmethod
    def _get_bucket_name(domain: Domain) -> str:
        return TemplatesBucket.BUCKET.format(domain=domain.value)

    @staticmethod
    def _get_template_spec_key(template: str) -> str:
        return f"{TemplatesBucket._get_template_prefix(template)}{TemplatesBucket.TEMPLATE_SPEC}"

    @staticmethod
    def _get_template_key(template: str) -> str:
        return f"{TemplatesBucket._get_template_prefix(template)}{TemplatesBucket.TEMPLATE}"

    @staticmethod
    def _get_assets_prefix(template: str) -> str:
        return TemplatesBucket.ASSETS_DIR.format(
            templates_dir=TemplatesBucket.TEMPLATES_DIR, template=template
        )

    @staticmethod
    def _get_template_prefix(template: str) -> str:
        return TemplatesBucket.TEMPLATE_DIR.format(
            templates_dir=TemplatesBucket.TEMPLATES_DIR, template=template
        )
