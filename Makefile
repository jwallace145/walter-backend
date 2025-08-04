.PHONY: help install lint test format run

help:
	@echo "Common commands:"
	@echo "  make format         	  Auto-format code"
	@echo "  make lint                Lint code"
	@echo "  make test    	     	  Run unit test suite"
	@echo "  make update-src     	  Update Walter API src code"
	@echo "  make update-image   	  Update WalterAPI image"
	@echo "  make update-infra        Update Walter API infra"


format:
	pipenv run black .

lint:
	pipenv run flake8 src --count --max-complexity=10 --max-line-length=127 --show-source --statistics --ignore=E203,E501,W503,C901,W291

test:
	pipenv run pytest --cov src --cov-report=xml -vv

update-image:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 010526272437.dkr.ecr.us-east-1.amazonaws.com \
	&& docker build -t walter/api . \
	&& docker tag walter/api:latest 010526272437.dkr.ecr.us-east-1.amazonaws.com/walter/api:latest \
	&& docker push 010526272437.dkr.ecr.us-east-1.amazonaws.com/walter/api:latest

update-src:
	echo "Updating Walter backend source code" \
	&& mkdir walter-backend \
	&& cp -r src walter-backend \
	&& cp config.yml walter-backend \
	&& cp walter.py walter-backend \
	&& cd walter-backend \
	&& zip -r ../walter-backend.zip . \
	&& cd .. \
	&& echo "Publishing Walter backend source to S3" \
	&& aws s3 cp walter-backend.zip s3://walter-backend-src/walter-backend.zip \
	&& rm -rf walter-backend \
	&& rm -rf walter-backend.zip

update-infra:
	pipenv run python buildspec.py