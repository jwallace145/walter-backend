aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 010526272437.dkr.ecr.us-east-1.amazonaws.com \
&& docker build -t walter/api . \
&& docker tag walter/api:latest 010526272437.dkr.ecr.us-east-1.amazonaws.com/walter/api:latest \
&& docker push 010526272437.dkr.ecr.us-east-1.amazonaws.com/walter/api:latest