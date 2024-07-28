### WalterAI

WalterAI is a bot that sends daily emails to subscribed users at 8:00am sharp about movements in the markets their following. 

### Architecture

WalterAI is hosted on website `https://walterai.io` where users 

The Walter backend code is deployed to AWS Lambda and invoked by EventBridge at 9:00am sharp. Walter is stateless and pulls market data from Polygon on each invocation and generates reports to email to subscribed users. The markets Walter follows are stored in DynamoDB and added by users. Each email generated will be dumped to S3 before being emailed via SES.

```
# create development stack
aws cloudformation create-stack \
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

# upload src code to s3 and update lambda function
mkdir walterai-backend \
&& cp -r src walterai-backend \
&& cp walter_ai.py walterai-backend \
&& cd walterai-backend \
&& zip -r ../walterai-backend.zip . \
&& cd .. \
&& rm -rf walterai-backend \
&& aws s3 cp walterai-backend.zip s3://walterai-backend-src/walterai-backend.zip \
&& rm -rf walterai-backend.zip \
&& aws lambda update-function-code \
  --function-name="WalterAIBackend-dev" \
  --s3-bucket walterai-backend-src \
  --s3-key walterai-backend.zip
```

### Contributions

* [Black: The uncompromising code formatter](https://black.readthedocs.io/en/stable/)
* [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
* [Pre-Commit](https://github.com/pre-commit/pre-commit)


### Links

* [Polygon IO Python Client](https://github.com/polygon-io/client-python)
* [Pre-Commit](https://github.com/pre-commit/pre-commit)