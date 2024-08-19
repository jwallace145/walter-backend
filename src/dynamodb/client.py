from dataclasses import dataclass
from typing import List

from mypy_boto3_dynamodb import DynamoDBClient
from src.environment import Domain
from src.utils.log import Logger
from botocore.exceptions import ClientError

log = Logger(__name__).get_logger()


@dataclass
class WalterDDBClient:
    """
    WalterAI DDB Client
    """

    client: DynamoDBClient
    domain: Domain

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} DDB client in region '{self.client.meta.region_name}'"
        )

    def put_item(self, table: str, item: dict) -> None:
        log.info(f"Adding item to table '{table}':\n{item}")
        try:
            self.client.put_item(TableName=table, Item=item)
        except ClientError as error:
            log.error(
                f"Unexpected error occurred putting item to '{table}'!\n"
                f"Error: {error.response['Error']['Message']}"
            )

    def query(self, table: str, query: dict) -> List[dict]:
        log.info(f"Querying items in table '{table}' with query:\n{query}")
        try:
            return self.client.query(TableName=table, KeyConditions=query)["Items"]
        except ClientError as error:
            log.error(
                f"Unexpected error occurred querying items from table '{table}'!\n"
                f"Error: {error.response['Error']['Message']}"
            )

    def get_item(self, table: str, key: dict) -> dict:
        log.info(f"Getting item from table '{table}' with key:\n{key}")
        try:
            return self.client.get_item(TableName=table, Key=key)
        except ClientError as error:
            log.error(
                f"Unexpected error occurred getting item from '{table}'!\n"
                f"Error: {error.response['Error']['Message']}"
            )

    def scan_table(self, table: str) -> List[dict]:
        log.info(f"Scanning table '{table}'")
        try:
            return self.client.scan(TableName=table)["Items"]
        except ClientError as error:
            log.error(
                f"Unexpected error occurred attempting to scan table '{table}'!\n"
                f"Error: {error.response['Error']['Message']}"
            )
