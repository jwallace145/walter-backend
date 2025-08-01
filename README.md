### WalterBackend

[![Walter](https://img.shields.io/badge/Walter-555555)](https://walterai.dev) ![Python Version](https://img.shields.io/badge/Python-3.12-green) [![codecov](https://codecov.io/gh/jwallace145/walter-backend/graph/badge.svg?token=OKI43GAC28)](https://codecov.io/gh/jwallace145/walter-backend)

[`Walter`](`https://walterai.io`) is an artificially intelligent bot that creates and sends customized newsletters to subscribers at 7:00am sharp about the markets they're following. `WalterAI` gathers market data from various APIs for each user and their interested stocks and feeds the data into [Bedrock](https://aws.amazon.com/bedrock/) to get AI insights from the LLM [Meta Llama 3](https://ai.meta.com/blog/meta-llama-3/). This allows `WalterAI` to create tailored newsletters for each subscriber including information only about the markets relevant to the user's portfolio.

`WalterAIBackend` is the backend service that maintains the database of subscribers and their interested stocks as well as the service responsible for creating and sending the customized newsletters. `WalterAIBackend` is powered completely by [AWS](https://aws.amazon.com/) and runs on [Lambda](https://aws.amazon.com/lambda/). 

### Table of Contents

* [Walter](#walter)
* [Table of Contents](#table-of-contents)
* [Architecture](#architecture)
* [Templates](#templates)
* [Contributions](#contributions)
* [Links](#links)

### Features

* Track expenses with intelligent-categorization
* Track portfolio performance with AI insights
* Deliver weekly financial wellness newsletters

### Architecture

![Walter-ArchDiagram](https://github.com/user-attachments/assets/5cbac20f-8366-4904-a5b5-0b2a43eb669c)

### Templates

`WalterAIBackend` uses email templates stored in S3 to create the emails to send to subscribers. Each email template is written in HTML and uses [Jinja](https://jinja.palletsprojects.com/en/3.1.x/api/) to parameterize the inputs. `WalterAIBackend` pulls the email templates from S3 and renders the template given the `templatespec.yml` and the `template.jinja` file. The `templatespec.yml` is the specification file that tells Walter the name of the parameters as well as the Bedrock prompts to use to get the parameter value. An example of a `templatespec.yml` file is given below:

```yaml
version: 0.0

#########################
# DEFAULT TEMPLATE SPEC #
#########################

TemplateSpec:

  ###########
  # CONTEXT #
  ###########

  Context:
    User: {{ user }}
    PortfolioValue: {{ portfolio_value }}
    Stocks:
      {% for stock in stocks %}
      - Symbol: {{ stock.symbol }}
        Price: {{ stock.price }}
      {% endfor %}

  ########
  # KEYS #
  ########

  Keys:
    - Key: User
      Value: {{ user }}
    - Key: PortfolioValue
      Value: {{ portfolio_value }}
      
  ###########
  # PROMPTS #
  ###########

  Prompts:
    - Key: Newsletter
      Prompt: |
        Write a newsletter with business casual humor!
      MaxGenLength: 600
```

After getting the answers to the prompts given in the `templatespec.yml` file, Walter renders the template with 
[Jinja](https://jinja.palletsprojects.com/en/3.1.x/api/) and then sends the custom newsletter to the subscriber!

### Local Testing

WalterAPI historically has used ZIP packages for Lambda deployments but ever since the addition of scikit-learn, the deployment package is now >250 MB and Walter can no longer use ZIP packages...

So, WalterAPI is forced to use container images for the Lambdas! Woot woot, deployment packages can be up to 10 GB in size now (I think, surely more than >250 MB). However, local testing just got a bit harder...

I can still test WalterAPI locally with the API containers but need to utilize the [AWS Lambda Runtime Interface Emulator](https://github.com/aws/aws-lambda-runtime-interface-emulator) as it sents up the HTTP server that is usually orchestrated by API Gateway. The HTTP server created by the AWS Lambda RIE accepts incoming curl requests and marshals the request to JSON that the Lambda container can understand and process.

The AWS RIE is included in AWS base images which WalterAPIs utilize so no issue installing it. However, coming up with the command to invoke a Lambda behind an API with AWS RIE was a bit troublesome. Putting the commands here for later reference and until I find a better place to put this stuff...

#### Build Docker Image

```bash
docker build -t walter/api:latest . 
```

#### Docker Run AWS Lambda RIE

AWS Lambda RIE runs on port 9000 and needs creds exported as env vars to make authenticated AWS API calls. 

```bash
docker run -p 9000:8080 --env-file .env walter/api:latest walter.auth_user_entrypoint
```

#### Invoke WalterAPI Container via AWS Lambda RIE
```bash
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{
        "headers": {
          "Content-Type": "application/json"
        },
        "body": "{\"email\": \"testuser@walterai.dev\", \"password\": \"testpassword\"}"
      }' | jq -r '.body | fromjson'
```

### Contributions

#### Makefile

This repository contains a `Makefile` with commands to perform common tasks such as code formatting and linting, running the unit suite, and deploying code updates to designated environments. 

To learn more about the included commands and their function, view the `Makefile` or run the below help command:

```bash
# view the help message for the commands included
make help

# for example, run the following command to format source code
make format
```

#### CLI Development Tool

This repository includes a command-line interface (CLI) tool built with [Typer](https://typer.tiangolo.com/) that
enables developers to test and interact with the Walter API in their local development environment. The CLI uses the
local source code allowing you to test code changes and modifications without deploying to production. Ensure that you are leveraging credentials for a nonproduction environment as to not modify customer resources.

To explore available methods and their required arguments, use the
following commands:

```bash
# display cli help message and all included methods
pipenv run python cli.py --help

# display more information about cli method
pipenv run python cli.py "${METHOD_NAME}" --help
```

To interact with an authenticated Walter API method, an API access token is required that identifies the user. Run the following command to use the CLI tool to get an access token for a user:

```bash
# get access token for user
pipenv run python auth-user --email="${EMAIL}" --password="${PASSWORD}"

# export token as env var to be used for authenticated methods
export WALTER_TOKEN=ABC123
```

### Dependencies

* [AlphaVantage](https://www.alphavantage.co/documentation/)
* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/index.html)
* [Jinja](https://jinja.palletsprojects.com/en/stable/)
* [Meta Llama 3](https://ai.meta.com/blog/meta-llama-3/)
* [Polygon](https://polygon.io/)

### Contributions

* [Black: The uncompromising code formatter](https://black.readthedocs.io/en/stable/)
* [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
* [Pre-Commit](https://github.com/pre-commit/pre-commit)
* [Codecov](https://about.codecov.io/)



