echo "Updating Walter default templates" \
&& echo "Updating Walter default template spec..." \
&& aws s3 cp ./templates/default/templatespec.jinja s3://walterai-templates-dev/templates/default/templatespec.jinja \
&& aws echo "Updating Walter default template..." \
&& aws s3 cp ./templates/default/template.jinja s3://walterai-templates-dev/templates/default/template.jinja