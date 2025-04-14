### WalterBackend

[![Walter](https://img.shields.io/badge/Walter-555555)](https://walterai.dev) ![Python Version](https://img.shields.io/badge/Python-3.11-green) [![codecov](https://codecov.io/gh/jwallace145/walter-backend/graph/badge.svg?token=OKI43GAC28)](https://codecov.io/gh/jwallace145/walter-backend)

[`Walter`](`https://walterai.io`) is an artificially intelligent bot that creates and sends customized newsletters to subscribers at 7:00am sharp about the markets they're following. `WalterAI` gathers market data from various APIs for each user and their interested stocks and feeds the data into [Bedrock](https://aws.amazon.com/bedrock/) to get AI insights from the LLM [Meta Llama 3](https://ai.meta.com/blog/meta-llama-3/). This allows `WalterAI` to create tailored newsletters for each subscriber including information only about the markets relevant to the user's portfolio.

`WalterAIBackend` is the backend service that maintains the database of subscribers and their interested stocks as well as the service responsible for creating and sending the customized newsletters. `WalterAIBackend` is powered completely by [AWS](https://aws.amazon.com/) and runs on [Lambda](https://aws.amazon.com/lambda/). 

### Table of Contents

* [Walter](#walter)
* [Table of Contents](#table-of-contents)
* [Architecture](#architecture)
* [Templates](#templates)
* [Contributions](#contributions)
* [Links](#links)

### Architecture

![Walter-ArchDiagram-2025-04](https://github.com/user-attachments/assets/836c3e29-bcef-4c6d-a754-5159ed1416e4)

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



