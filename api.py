import json


def lambda_handler(event, context) -> dict:
    return {"statusCode": 200, "body": json.dumps("WalterAPI")}
