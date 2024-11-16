echo "Updating Walter verify templates" \
&& echo "Updating Walter verify template spec..." \
&& aws s3 cp ./templates/verify/templatespec.jinja s3://walterai-templates-dev/templates/verify/templatespec.jinja \
&& echo "Updating Walter verify template..." \
&& aws s3 cp ./templates/verify/template.jinja s3://walterai-templates-dev/templates/verify/template.jinja