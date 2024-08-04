### WalterAIBackend

[`WalterAI`](`https://walterai.io`) is a bot that sends subscribed users daily emails about the stocks they're interested in with market data provided by [Polygon](https://polygon.io/) and generative AI responses by [Meta Llama 3](https://ai.meta.com/blog/meta-llama-3/) powered by [AWS](https://aws.amazon.com/).

`WalterAIBackend` is the backend service that interacts with the [DynamoDB](https://aws.amazon.com/dynamodb/) databases and gets stock market data to feed into the [Amazon Bedrock](https://aws.amazon.com/bedrock/) models to generate the daily newsletter. `WalterAIBackend` is implemented as a [Lambda](https://aws.amazon.com/lambda/) function and handles different events to add users and stocks to DDB as well as send emails via [SES](https://aws.amazon.com/ses/). This service is invoked at 8:00am (EST) sharp by an [EventBridge](https://aws.amazon.com/eventbridge/) trigger and also on-demand by users.

### Scripts

```
# create development stack
&& aws cloudformation create-stack \
  --stack-name="WalterAIBackend-Dev" \
  --template-body="file://infra/infra.yml" \
  --parameters="ParameterKey=AppEnvironment,ParameterValue=dev" \
  --capabilities="CAPABILITY_NAMED_IAM"

# update development stack
aws cloudformation update-stack \
  --stack-name="WalterAIBackend-Dev" \
  --template-body="file://infra/infra.yml" \
  --parameters="ParameterKey=AppEnvironment,ParameterValue=dev" \
  --capabilities="CAPABILITY_NAMED_IAM"

# create lambda layer, bump lambda layer version in cfn template
mkdir python \
&& pipenv lock --requirements > requirements.txt \
&& pip3 install -r requirements.txt --platform manylinux2014_aarch64 --target ./python --only-binary=:all: --upgrade \
&& zip -r python.zip python \
&& aws lambda publish-layer-version \
  --layer-name WalterAILambdaLayer \
  --zip-file fileb://python.zip \
  --compatible-runtimes python3.11 \
  --compatible-architectures "arm64" \
&& rm -rf python* \
&& rm -rf requirements.txt
```

### Contributions

* [Black: The uncompromising code formatter](https://black.readthedocs.io/en/stable/)
* [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
* [Pre-Commit](https://github.com/pre-commit/pre-commit)


### Links

* [Polygon IO Python Client](https://github.com/polygon-io/client-python)
* [Pre-Commit](https://github.com/pre-commit/pre-commit)