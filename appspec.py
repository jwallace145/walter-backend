import boto3

APPSPEC_TEMPLATE = """
version: 0.0

Resources:
  - MyFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: "WalterAIBackend-dev"
        Alias: "WalterAIBackend-dev"
        CurrentVersion: "{current_version}"
        TargetVersion: "{target_version}"
"""

with open("./appspec.yml", "w") as appspec:
    lambda_client = boto3.client("lambda", region_name="us-east-1")
    current_version = lambda_client.get_alias(
        FunctionName="WalterAIBackend-dev", Name="WalterAIBackend-dev"
    )["FunctionVersion"]
    target_version = lambda_client.list_versions_by_function(
        FunctionName="WalterAIBackend-dev"
    )["Versions"][-1]["Version"]
    appspec.write(
        APPSPEC_TEMPLATE.format(
            current_version=current_version, target_version=target_version
        )
    )
