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