import os
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from botocore.exceptions import ClientError
from mypy_boto3_ses import SESClient
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SESClient:
    """
    WalterAI Simple Email Service (SES) Client
    """

    SENDER = "walteraifinancialadvisor@gmail.com"  # TODO: send from a verified domain
    CHARSET = "utf-8"

    client: SESClient
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} SES Client in region '{self.client.meta.region_name}'"
        )

    def send_email(
        self, recipient: str, body: str, subject: str, images: List[str]
    ) -> None:
        log.info(
            f"Sending email to recipient '{recipient}' from sender '{SESClient.SENDER}'"
        )
        email = SESClient._create_email(
            SESClient.SENDER, recipient, subject, body, images
        )
        try:
            self.client.send_raw_email(
                Source=SESClient.SENDER,
                Destinations=[recipient],
                RawMessage={
                    "Data": email.as_string(),
                },
            )
            log.info(f"Successfully sent email to recipient '{recipient}'")
        except ClientError as exception:
            log.error(
                f"Unexpected error occurred attempting to send email to recipient '{recipient}'! Exception: {exception.response['Error']['Message']}"
            )

    @staticmethod
    def _create_email(
        sender: str, recipient: str, subject: str, body: str, images: List[str]
    ) -> MIMEMultipart:
        log.info(f"Creating MIMEMultipart email for recipient '{recipient}'")
        email = MIMEMultipart("mixed")
        email["From"] = SESClient.SENDER
        email["To"] = recipient
        email["Subject"] = subject
        email_body = MIMEMultipart("alternative")
        html_body = MIMEText(body.encode(SESClient.CHARSET), "html", SESClient.CHARSET)
        email_body.attach(html_body)
        email.attach(email_body)
        log.info("Adding images to email")
        for image in images:
            image_name = image.split("/")[-1].split(".")[0]
            log.info(f"Adding image '{image_name}' to email as an attachment")
            attachment = MIMEApplication(open(image, "rb").read())
            attachment.add_header("Content-ID", f"<{image_name}>")
            attachment.add_header(
                "Content-Disposition", "inline", filename=os.path.basename(image_name)
            )
            email.attach(attachment)
        return email
