#!/bin/bash

set -e

ENVIRONMENT=$1
ACTION=${2:-apply}

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment> [plan|apply|destroy]"
    echo "Environments: dev, stg, prod"
    exit 1
fi

if [ ! -d "./infra/environments/$ENVIRONMENT" ]; then
    echo "Environment $ENVIRONMENT not found"
    exit 1
fi

echo "🚀 Running Terraform $ACTION for $ENVIRONMENT environment"

# Change to infrastructure directory
cd ./infra/infrastructure

# Initialize Terraform with backend configuration
terraform init -backend-config="../environments/$ENVIRONMENT/backend.tfbackend"

# Run the specified action
case $ACTION in
    plan)
        terraform plan -var-file="../environments/$ENVIRONMENT/terraform.tfvars"
        ;;
    apply)
        terraform apply -var-file="../environments/$ENVIRONMENT/terraform.tfvars"
        ;;
    destroy)
        terraform destroy -var-file="../environments/$ENVIRONMENT/terraform.tfvars"
        ;;
    *)
        echo "Invalid action: $ACTION"
        echo "Valid actions: plan, apply, destroy"
        exit 1
        ;;
esac