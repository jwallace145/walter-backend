### Walter

[![codecov](https://codecov.io/gh/jwallace145/walter/graph/badge.svg?token=OKI43GAC28)](https://codecov.io/gh/jwallace145/walter)

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

![image](https://github.com/user-attachments/assets/c484bd63-0381-4045-8039-a9f79ecc12fc)


### Templates

`WalterAIBackend` uses email templates stored in S3 to create the emails to send to subscribers. Each email template is written in HTML and uses [Jinja](https://jinja.palletsprojects.com/en/3.1.x/api/) to parameterize the inputs. `WalterAIBackend` pulls the email templates from S3 and renders the template given the `templatespec.yml` and the `template.jinja` file. The `templatespec.yml` is the specification file that tells Walter the name of the parameters as well as the Bedrock prompts to use to get the parameter value. An example of a `templatespec.yml` file is given below:

```yaml
version: 0.0

TemplateSpec:
  Parameters:
    - Key: Introduction # template includes a key "Introduction"
      Prompt: | # Bedrock prompt for "Introduction" 
        Introduce yourself as Walter, a friendly AI financial newsletter bot
      MaxGenLength: 100
    - Key: DailyJoke # template includes a key "DailyJoke"
      Prompt: | # Bedrock prompt for "DailyJoke"
        Tell a joke!
      MaxGenLength: 50
```

After getting the answers to the prompts given in the `templatespec.yml` file, Walter renders the template with 
[Jinja](https://jinja.palletsprojects.com/en/3.1.x/api/) and then sends the custom newsletter to the subscriber!

### Contributions

* [Black: The uncompromising code formatter](https://black.readthedocs.io/en/stable/)
* [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
* [Pre-Commit](https://github.com/pre-commit/pre-commit)
* [Codecov](https://about.codecov.io/)


### Links

* [Polygon IO Python Client](https://github.com/polygon-io/client-python)
* [Pre-Commit](https://github.com/pre-commit/pre-commit)
