echo "Updating Walter change_password templates" \
&& echo "Updating Walter change_password template spec..." \
&& aws s3 cp ./templates/change_password/templatespec.jinja s3://walterai-templates-dev/templates/change_password/templatespec.jinja \
&& echo "Updating Walter change_password template..." \
&& aws s3 cp ./templates/change_password/template.jinja s3://walterai-templates-dev/templates/change_password/template.jinja