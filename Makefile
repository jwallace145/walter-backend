.PHONY: help install lint test format run

help:
	@echo "Common commands:"
	@echo "  make format         	  Auto-format code"
	@echo "  make lint                Lint code"
	@echo "  make test    	     	  Run unit test suite"
	@echo "  make deploy              Deploy changes"


format:
	pipenv run black .

lint:
	pipenv run flake8 src --count --max-complexity=10 --max-line-length=127 --show-source --statistics --ignore=E203,E501,W503,C901,W291

test:
	pipenv run pytest --cov src --cov-report=xml -vv

deploy:
	pipenv run python deploy.py