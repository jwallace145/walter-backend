##############
# WALTER API #
##############

# To browse AWS Lambda Python base images: https://gallery.ecr.aws/lambda/python
# AWS Lambda Python 3.12 base image includes the
# AWS Lambda Runtime Interface Emulator (RIE) by default
FROM public.ecr.aws/lambda/python:3.12-arm64

# install pipenv to convert Pipfile to requirements.txt file
# to install with pip
RUN pip install pipenv

# copy Pipfile before dumping to requirements.txt file
COPY Pipfile ${LAMBDA_TASK_ROOT}/
COPY Pipfile.lock ${LAMBDA_TASK_ROOT}/

# set work dir
WORKDIR ${LAMBDA_TASK_ROOT}

# dump Pipfile to requirements file and install them with pip
RUN pipenv requirements > requirements.txt && \
    pip install -r requirements.txt

# install datadog lambda extension to forward metrics and logs to datadog
COPY --from=public.ecr.aws/datadog/lambda-extension:latest /opt/. /opt/

# copy application source code, entrypoints file, and configurations
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY walter.py ${LAMBDA_TASK_ROOT}/
COPY config.yml ${LAMBDA_TASK_ROOT}/
COPY expense_category_encoder.pkl ${LAMBDA_TASK_ROOT}/
COPY expense_categorization_pipeline.pkl ${LAMBDA_TASK_ROOT}/

# Override the command for each component to use the correct entrypoint, see walter.py
CMD [ "OVERRIDE ME!" ]