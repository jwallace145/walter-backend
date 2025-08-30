.PHONY: help install lint test format run plan apply destroy

help:
	@echo "Common commands:"
	@echo "  make format		 	  Auto-format code"
	@echo "  make lint				Lint code"
	@echo "  make test			 	  Run unit test suite"
	@echo "  make deploy			  Deploy changes"
	@echo "  make docs				Push updates to API documentation website"
	@echo "  make plan domain=<env>   Plan infrastructure changes for environment"
	@echo "  make apply domain=<env>  Apply infrastructure changes for environment"
	@echo "  make destroy domain=<env> Destroy infrastructure for environment"


format:
	pipenv run black . && pipenv run isort . --profile black && terraform fmt -check -recursive

lint:
	pipenv run flake8 src --count --max-complexity=10 --max-line-length=127 --show-source --statistics --ignore=E203,E501,W503,C901,W291

test:
	pipenv run pytest --cov src --cov-report=xml -vv

deploy:
	pipenv run python deploy.py

docs:
	aws s3 cp ./openapi.yml s3://walterapi-docs/openapi.yml --content-type application/yaml

plan:
	@if [ "$(domain)" != "dev" ] && [ "$(domain)" != "stg" ] && [ "$(domain)" != "prod" ]; then \
		echo "Error: domain must be dev, stg, or prod"; \
		exit 1; \
	fi
	./infra/scripts/plan.sh $(domain)

apply:
	@if [ "$(domain)" != "dev" ] && [ "$(domain)" != "stg" ] && [ "$(domain)" != "prod" ]; then \
		echo "Error: domain must be dev, stg, or prod"; \
		exit 1; \
	fi
	./infra/scripts/apply.sh $(domain)

destroy:
	@if [ "$(domain)" != "dev" ] && [ "$(domain)" != "stg" ] && [ "$(domain)" != "prod" ]; then \
		echo "Error: domain must be dev, stg, or prod"; \
		exit 1; \
	fi
	./infra/scripts/destroy.sh $(domain)