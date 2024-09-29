from dataclasses import dataclass
from typing import List

from botocore.exceptions import ClientError
from mypy_boto3_dynamodb import DynamoDBClient

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterDDBClient:
    """
    WalterAI DDB Client

    This client is a wrapper around the Boto3 DynamoDB client and is
    utilized by Walter to interact with all DDB tables.
    """

    client: DynamoDBClient

    def __post_init__(self) -> None:
        log.debug(
            f"Creating Walter DDB client in region '{self.client.meta.region_name}'"
        )

    def put_item(self, table: str, item: dict) -> None:
        """
        Put an item into the DDB table.

        Args:
            table: The name of the DDB table to insert the item.
            item: The item to insert into the DDB table.

        Returns:
            None.
        """
        log.debug(f"Adding item to table '{table}':\n{item}")
        try:
            self.client.put_item(TableName=table, Item=item)
        except ClientError as error:
            log.error(
                f"Unexpected error occurred putting item to '{table}'!\n"
                f"Error: {error.response['Error']['Message']}"
            )

    def query(self, table: str, query: dict) -> List[dict]:
        """
        Query for an item in a DDB table.

        Args:
            table: The name of the DDB table to query.
            query: The query expression to query against the DDB table.

        Returns:
            The list of DDB items that are returned by the query expression.
        """
        log.debug(f"Querying items in table '{table}' with query:\n{query}")
        try:
            return self.client.query(TableName=table, KeyConditions=query)["Items"]
        except ClientError as error:
            log.error(
                f"Unexpected error occurred querying items from table '{table}'!\n"
                f"Error: {error.response['Error']['Message']}"
            )

    def get_item(self, table: str, key: dict) -> dict:
        """
        Get an item from a DDB table given its primary key.

        Args:
            table: The name of the DDB table.
            key: The primary key of the item to retrieve.

        Returns:
            The DDB item of the item with the given primary key.
        """
        log.debug(f"Getting item from table '{table}' with key:\n{key}")
        try:
            return self.client.get_item(TableName=table, Key=key)["Item"]
        except ClientError as clientError:
            log.error(
                f"Unexpected error occurred getting item from '{table}'!\n"
                f"Error: {clientError.response['Error']['Message']}"
            )
        except KeyError:
            # key error thrown when trying to index ddb client response
            # i.e. the item does not exist
            return None

    def scan_table(self, table: str) -> List[dict]:
        """
        Scan the DDB table and return the list of items contained in the table.

        This operation is expensive as it scans the entire DDB table. Use this method
        with caution as there are performance implications.

        Args:
            table: The name of the DDB table to scan.

        Returns:
            The list of items contained in the DDB table.
        """
        log.debug(f"Scanning table '{table}'")
        try:
            return self.client.scan(TableName=table)["Items"]
        except ClientError as error:
            log.error(
                f"Unexpected error occurred attempting to scan table '{table}'!\n"
                f"Error: {error.response['Error']['Message']}"
            )
