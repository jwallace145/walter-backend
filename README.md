# WalterBackend

[![Walter](https://img.shields.io/badge/Walter-555555)](https://walterai.dev)  [![codecov](https://codecov.io/gh/jwallace145/walter-backend/graph/badge.svg?token=OKI43GAC28)](https://codecov.io/gh/jwallace145/walter-backend) [![Static Badge](https://img.shields.io/badge/WalterAPI-Documentation-green)](http://walterapi-docs.s3-website-us-east-1.amazonaws.com/)

[**Walter**](https://walterai.dev) is an AI-powered personal finance platform that provides a complete, real-time view of your financial life. Securely connect all your accounts — banking, credit, investments, and more — to track expenses, optimize budgets, and accelerate wealth building through intelligent automation.

### Key Features

- 🤖 **Intelligent Transaction Processing**
Machine learning automatically categorizes expenses and adapts to your unique spending patterns over time.
- 📊 **Unified Financial Dashboard** 
View assets, liabilities, investments, and cash flow in a single, real-time interface.
- 🔍 **AI-Powered Insights**
Discover spending trends, identify savings opportunities, and receive alerts for unusual activity or budget deviations.
- 🎯 **Advanced Retirement Planning**
Plan with confidence using Monte Carlo simulations and customizable assumptions.

Walter combines automation and intelligence to help you spend smarter, save faster, and reach your financial goals.


## Table of Contents

* [Walter](#walter)
* [Table of Contents](#table-of-contents)
* [Features](#features)
* [Architecture](#architecture)
* [API Documentation](#documentation)
* [Deployments](#deployments)
* [Contributions](#contributions)

### Architecture

![Walter-ArchDiagram](https://github.com/user-attachments/assets/5cbac20f-8366-4904-a5b5-0b2a43eb669c)


## API Documentation

Walter's REST API is fully documented using [OpenAPI 3.0](https://spec.openapis.org/oas/v3.0.0.html) specifications and provides interactive documentation through [Swagger UI](https://swagger.io/tools/swagger-ui/):

📖 **[WalterAPI Documentation](http://walterapi-docs.s3-website-us-east-1.amazonaws.com/)**

### Getting Started

1. **Explore the API** — Browse all available endpoints and their schemas in the interactive API documentation
2. **Test endpoints** — Click `Try it out` on any method to make live API calls directly from the browser
3. **Authenticate** — For protected endpoints, first call the `/auth` method with valid credentials to obtain an access token

### Authentication Flow

```bash
# 1. Get access token for user from Swagger UI
POST /auth/login
{
  "email": "user@example.com",
  "password": "your_password"
}

# 2. Use token in subsequent requests via the authorize button
Authorization: Bearer <your_access_token>
```

### Development Workflow

The API documentation is automatically generated from the OpenAPI specifications file `openapi.yml` and must stay in sync with the codebase:

#### Updating Documentation

```bash
# Deploy documentation changes to S3
make docs
```

**Important:** Always update `openapi.yml` when adding, modifying, or removing API endpoints to ensure documentation accuracy.


## Deployments

`WalterBackend` is deployed to AWS using an automated deployment pipeline powered by the `deploy.py` script. The deploy script is called by the `deploy.yml` [GitHub action](https://github.com/features/actions) on merges to `main` to ensure the production environment stays up to date with the latest changes. This ensures consistent, reliable deployments with zero-downtime updates.

### Automated Deployment Workflow

**🚀 All merges to the `main` branch automatically trigger a production deployment.**

The deployment process is fully automated and executes the following steps:

#### 1. **Documentation Update**
- Syncs the latest OpenAPI specifications to the documentation site
- Ensures API docs stay current with code changes

#### 2. **Container Build & Registry**
- Builds a new `WalterBackend` image with the latest source code
- Pushes the `WalterBackend` image to [Amazon ECR (Elastic Container Registry)](https://aws.amazon.com/ecr/)

#### 3. **Source Code Deployment**
- Updates the `WalterBackend` source code in the AWS environment

#### 4. **Traffic Routing**
- Publishes a new version of `WalterBackend` and updates the release alias
- Ensures all API methods call the latest version of `WalterBackend`

### Infrastructure Management

The AWS infrastructure is managed through [CloudFormation](https://aws.amazon.com/cloudformation/) templates with parameterized versioning powered by [Jinja](https://jinja.palletsprojects.com/en/stable/):

```yaml
# the latest version of WalterAPI is injected as a Jinja2 template parameter in the deploy.py script
WalterAPIAlias:
Type: AWS::Lambda::Alias
Properties:
  FunctionName: !Ref WalterAPI
  FunctionVersion: {{ walter_api_version }}
  Name: "release"
```

The `deploy.py` script dynamically updates these version parameters after each successful build, enabling:
- **Rollback capability** to previous versions
- **Infrastructure as Code (IaC)** with version tracking

## Contributing to Walter

We welcome contributions to Walter! This guide will help you set up your development environment and understand our workflow.

### Development Workflow

Walter follows [**trunk-based development**](https://trunkbaseddevelopment.com/) with short-lived feature branches:

1. **Create a feature branch** from `main` for your changes
2. **Develop locally** using the CLI tool and Makefile commands
3. **Test thoroughly** in a non-production environment
4. **Open a merge request** to `main` with test artifacts
5. **Automated production deployment** occurs after successful merge to `main`

### Development Tools

#### Makefile Commands

The `Makefile` provides shortcuts for common development tasks:

```bash
# View all available commands
make help

# Code quality and testing
make format         # Format code with Black
make lint           # Run Flake8 linting
make test           # Execute unit tests with Pytest

# Development workflow
make docs         # Deploy documentation changes to S3
make deploy       # Deploy changes to specified environment
```

#### CLI Development Tool

Test your changes locally without deploying to AWS using the built-in CLI tool powered by [Typer](https://typer.tiangolo.com/):

```bash
# Explore available CLI methods
pipenv run python cli.py --help

# Get help for specific methods
pipenv run python cli.py "${METHOD_NAME}" --help

# Authenticate and get access token
pipenv run python cli.py auth-user --email="${EMAIL}" --password="${PASSWORD}"

# Export token for authenticated API calls
export WALTER_TOKEN=your_access_token_here
```

**Important:** Always use non-production AWS credentials to avoid modifying customer data.

### Code Quality Standards

#### Pre-commit Hooks

All contributions must pass automated quality checks before being pushed:

- [**Black**](https://black.readthedocs.io/en/stable/) - Code formatting
- [**Flake8**](http://flake8.pycqa.org/en/latest/) - Python linting  
- [**Codespell**](https://github.com/codespell-project/codespell) - Spelling validation
- [**Pytest**](https://docs.pytest.org/en/stable/) - Unit test execution

Pre-commit hooks prevent commits that fail these checks from being pushed to the repository. See the [pre-commit](https://pre-commit.com/) documentation and `.pre-commit-config.yaml` file for more information.

#### Setting Up Pre-commit

```bash
# Install pre-commit hooks
pre-commit install

# Run checks manually
pre-commit run --all-files
```

### Testing & Coverage

#### Local Testing

```bash
# Run the full test suite
make test

# Run specific tests
pipenv run pytest tests/test_specific_module.py

# Run with coverage report
pipenv run pytest --cov=walter_backend
```

#### Codecov Integration

On merge request creation, [Codecov](https://codecov.io/) automatically:
- Runs the complete test suite
- Calculates code coverage metrics
- Posts detailed coverage reports as comments
- Blocks merges if coverage drops below thresholds

### Merge Request Process

1. **Pre-deployment Testing**
   - Deploy your changes to a non-production environment
   - Include test results and validation artifacts in your MR description

2. **Code Review**
   - All code changes require review before merging
   - Address feedback and ensure all checks pass

3. **Automated Deployment**
   - Successful merges to `main` automatically deploy to production
   - Monitor deployment logs and service health post-merge

### Best Practices

- **Keep branches short-lived** (< 3 days preferred)
- **Write descriptive commit messages** following [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
- **Include tests** for all new functionality
- **Update documentation** for API changes
- **Test in non-prod** before opening merge requests
- **Monitor post-deployment** for any issues

### Getting Help

- Check the `Makefile` for available development commands
- Use `--help` flags with CLI commands for detailed usage
- Review existing tests for examples and patterns
- Open an issue for questions or suggestions



