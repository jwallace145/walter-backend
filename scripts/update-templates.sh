echo "Updating Walter default templates" \
&& echo "Updating Walter default template spec..." \
&& aws s3 cp ./templates/default/templatespec.jinja s3://walterai-templates-dev/templates/default/templatespec.jinja \
&& echo "Updating Walter default template..." \
&& aws s3 cp ./templates/default/template.jinja s3://walterai-templates-dev/templates/default/template.jinja \
&& echo "Updating Walter The Good The Bad template spec..." \
&& aws s3 cp ./templates/the_good_the_bad/templatespec.jinja s3://walterai-templates-dev/templates/the_good_the_bad/templatespec.jinja \
&& echo "Updating Walter The Good The Bad template..." \
&& aws s3 cp ./templates/the_good_the_bad/template.jinja s3://walterai-templates-dev/templates/the_good_the_bad/template.jinja