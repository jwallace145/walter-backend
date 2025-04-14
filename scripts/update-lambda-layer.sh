mkdir python \
&& pipenv requirements > requirements.txt \
&& pip3 install -r requirements.txt --platform manylinux2014_aarch64 --target ./python --only-binary=:all: --upgrade \
&& zip -r python.zip python \
&& aws lambda publish-layer-version \
  --layer-name WalterBackendLambdaPythonDependencies \
  --zip-file fileb://python.zip \
  --compatible-runtimes python3.11 \
  --compatible-architectures "arm64" \
&& rm -rf python* \
&& rm -rf requirements.txt