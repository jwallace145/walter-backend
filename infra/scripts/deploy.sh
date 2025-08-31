#!/bin/bash

set -e

ENVIRONMENT=$1
ACTION=${2:-apply}
SECRET_NAME="WalterBackendDatadogAPIKey"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if AWS CLI is installed and configured
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi

    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure' or set environment variables."
        exit 1
    fi

    log_success "AWS CLI is configured"
}

# Function to retrieve Datadog credentials from Secrets Manager
get_datadog_credentials() {
    log_info "Retrieving Datadog credentials from AWS Secrets Manager..."

    # Get the secret value
    local secret_json
    if ! secret_json=$(aws secretsmanager get-secret-value \
        --region "us-east-1" \
        --secret-id "$SECRET_NAME" \
        --query SecretString \
        --output text 2>/dev/null); then
        log_error "Failed to retrieve secret '$SECRET_NAME' from Secrets Manager"
        log_error "Please ensure:"
        log_error "  1. The secret exists in your current AWS region"
        log_error "  2. You have permissions to access the secret"
        log_error "  3. The secret name is correct: $SECRET_NAME"
        exit 1
    fi

    # Parse the JSON and extract all three keys
    local datadog_api_key datadog_app_key datadog_api_url
    if ! datadog_api_key=$(echo "$secret_json" | jq -r '.DATADOG_API_KEY' 2>/dev/null); then
        log_error "Failed to parse secret JSON or extract DATADOG_API_KEY"
        log_error "Expected JSON format: {\"DATADOG_API_KEY\": \"your-api-key\", \"DATADOG_APP_KEY\": \"your-app-key\", \"DATADOG_API_URL\": \"us5.datadoghq.com\"}"
        exit 1
    fi

    if ! datadog_app_key=$(echo "$secret_json" | jq -r '.DATADOG_APP_KEY' 2>/dev/null); then
        log_error "Failed to extract DATADOG_APP_KEY from secret"
        log_error "Expected JSON format: {\"DATADOG_API_KEY\": \"your-api-key\", \"DATADOG_APP_KEY\": \"your-app-key\", \"DATADOG_API_URL\": \"us5.datadoghq.com\"}"
        exit 1
    fi

    if ! datadog_api_url=$(echo "$secret_json" | jq -r '.DATADOG_API_URL' 2>/dev/null); then
        log_error "Failed to extract DATADOG_API_URL from secret"
        log_error "Expected JSON format: {\"DATADOG_API_KEY\": \"your-api-key\", \"DATADOG_APP_KEY\": \"your-app-key\", \"DATADOG_API_URL\": \"us5.datadoghq.com\"}"
        exit 1
    fi

    # Check if all keys were extracted successfully
    if [ "$datadog_api_key" == "null" ] || [ -z "$datadog_api_key" ]; then
        log_error "DATADOG_API_KEY not found in secret or is empty"
        log_error "Please ensure the secret contains all required keys"
        exit 1
    fi

    if [ "$datadog_app_key" == "null" ] || [ -z "$datadog_app_key" ]; then
        log_error "DATADOG_APP_KEY not found in secret or is empty"
        log_error "Please ensure the secret contains all required keys"
        exit 1
    fi

    if [ "$datadog_api_url" == "null" ] || [ -z "$datadog_api_url" ]; then
        log_error "DATADOG_API_URL not found in secret or is empty"
        log_error "Please ensure the secret contains all required keys"
        exit 1
    fi

    # Export as environment variables for Terraform
    export DD_API_KEY="$datadog_api_key"
    export DD_APP_KEY="$datadog_app_key"
    export DD_HOST="$datadog_api_url"
    log_success "Datadog credentials and site configuration retrieved and set as environment variables"
}

# Function to check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install it first."
        log_error "  macOS: brew install jq"
        log_error "  Ubuntu/Debian: sudo apt-get install jq"
        log_error "  CentOS/RHEL: sudo yum install jq"
        exit 1
    fi
}

# Function to validate inputs
validate_inputs() {
    if [ -z "$ENVIRONMENT" ]; then
        log_error "Environment is required"
        echo "Usage: $0 <environment> [plan|apply|destroy]"
        echo "Environments: dev, stg, prod"
        exit 1
    fi

    if [ ! -d "./infra/environments/$ENVIRONMENT" ]; then
        log_error "Environment '$ENVIRONMENT' not found"
        log_error "Available environments:"
        ls -1 ./infra/environments/ 2>/dev/null || log_error "No environments directory found"
        exit 1
    fi

    case $ACTION in
        plan|apply|destroy)
            log_success "Action '$ACTION' is valid"
            ;;
        *)
            log_error "Invalid action: $ACTION"
            echo "Valid actions: plan, apply, destroy"
            exit 1
            ;;
    esac
}

# Function to run terraform
run_terraform() {
    log_info "Running Terraform $ACTION for $ENVIRONMENT environment"

    # Change to infrastructure directory
    cd ./infra/infrastructure

    # Initialize Terraform with backend configuration
    log_info "Initializing Terraform..."
    if ! terraform init -backend-config="../environments/$ENVIRONMENT/backend.tfbackend"; then
        log_error "Terraform init failed"
        exit 1
    fi

    # Run the specified action
    case $ACTION in
        plan)
            log_info "Running Terraform plan..."
            terraform plan -var-file="../environments/$ENVIRONMENT/terraform.tfvars"
            ;;
        apply)
            log_info "Running Terraform apply..."
            terraform apply -var-file="../environments/$ENVIRONMENT/terraform.tfvars"
            ;;
        destroy)
            log_warning "Running Terraform destroy..."
            log_warning "This will destroy resources in the $ENVIRONMENT environment!"
            read -p "Are you sure? (yes/no): " -r
            if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                terraform destroy -var-file="../environments/$ENVIRONMENT/terraform.tfvars"
            else
                log_info "Destroy cancelled"
                exit 0
            fi
            ;;
    esac
}

# Function to cleanup sensitive environment variables
cleanup() {
    unset DD_API_KEY
    unset DD_APP_KEY
    log_info "Cleaned up sensitive environment variables"
}

# Main execution
main() {
    log_info "🚀 Starting deployment process..."

    # Validate inputs first
    validate_inputs

    # Check prerequisites
    check_aws_cli
    check_jq

    # Get Datadog credentials
    get_datadog_credentials

    # Set trap to cleanup on exit
    trap cleanup EXIT

    # Run Terraform
    run_terraform

    log_success "🎉 Deployment completed successfully!"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi