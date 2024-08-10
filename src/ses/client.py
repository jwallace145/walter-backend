import os
from dataclasses import dataclass
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
from typing import Dict

from botocore.exceptions import ClientError
from mypy_boto3_ses import SESClient
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SESClient:
    """
    Simple Email Service (SES) Client

    This client is responsible for sending emails to subscribed users given
    a recipient email address and an HTML email.

    Domains:
        - walterai.io # TODO: pending verification
        - walterai.dev # TODO: pending verification
    """

    SENDER = "walteraifinancialadvisor@gmail.com"  # TODO: send from a verified domain
    CHARSET = "utf-8"

    client: SESClient
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} SES client in region '{self.client.meta.region_name}'"
        )

    def send_email(
        self, recipient: str, body: str, subject: str, assets: Dict[str, BytesIO]
    ) -> None:
        """Send email to given recipient.

        This method creates an email to send via Amazon SES given the subect,
        body, and assets. After creating the MIME email, this method sends the
        email via the Boto3 SES client to the recipient.

        Args:
            recipient (str): The intended recipient of the email.
            body (str): The HTML body of the email.
            subject (str): The subject of the email.
            assets (Dict[str, StringIO]): The assets referenced by the HTML body.
        """
        log.info(
            f"Sending email to recipient '{recipient}' from sender '{SESClient.SENDER}'"
        )
        try:
            self.client.send_raw_email(
                Source=SESClient.SENDER,
                Destinations=[recipient],
                RawMessage={
                    "Data": SESClient._create_email(recipient, subject, body, assets),
                },
            )
            log.info(f"Successfully sent email to recipient '{recipient}'")
        except ClientError as exception:
            log.error(
                f"Unexpected error occurred attempting to send email to recipient '{recipient}'!\n"
                f"Exception: {exception.response['Error']['Message']}"
            )

    @staticmethod
    def _create_email(
        recipient: str, subject: str, body: str, assets: Dict[str, BytesIO]
    ) -> str:
        """Create an email to the given recipient.

        This method creates a MIME email to send to the given recipient.
        The created email will utilize the given subject and body and have
        links to the included assets in the HTML referenced via inline
        disposition. See for more info: https://stackoverflow.com/a/70812780

        Args:
            recipient (str): The intended recipient of the email.
            subject (str): The subject of the email.
            body (str): The HTML body of the email.
            assets (Dict[str, StringIO]): The assets referenced by the HTML body.

        Returns:
            str: The MIME email represented as a string.
        """
        # create mime email
        email = MIMEMultipart("mixed")

        # add sending information
        email["From"] = SESClient.SENDER
        email["To"] = recipient
        email["Subject"] = subject

        # add html body
        email_body = MIMEMultipart("alternative")
        html_body = MIMEText(body.encode(SESClient.CHARSET), "html", SESClient.CHARSET)
        email_body.attach(html_body)
        email.attach(email_body)

        # add assets as attachments
        for name, stream in assets.items():
            cid_name = name.split(".")[0]
            attachment = MIMEImage(stream.getvalue())
            attachment.add_header("Content-ID", f"<{cid_name}>")
            attachment.add_header(
                "Content-Disposition", "inline", filename=os.path.basename(cid_name)
            )
            email.attach(attachment)

        # return email as a string
        return email.as_string()
