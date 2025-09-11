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

# Function to retrieve Datadog credentials from shell
# used by Terraform to create Datadog resources like monitors
get_datadog_credentials() {
    log_info "Setting Datadog environment variables from TF_VAR values..."

    # Export as environment variables for Terraform
    export DD_API_KEY="$DATADOG_API_KEY"
    export DD_APP_KEY="$DATADOG_APP_KEY"
    export DD_HOST="$DATADOG_SITE"

    log_success "Datadog credentials and site configuration set as environment variables"
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

set_environment_variables() {
    # TODO: Support non "dev" environments

    # Define required environment variables
    required_vars=(
        "DATADOG_API_KEY"
        "DATADOG_APP_KEY"
        "DATADOG_SITE"
        "ACCESS_TOKEN_SECRET_KEY"
        "REFRESH_TOKEN_SECRET_KEY"
        "PLAID_CLIENT_ID"
        "PLAID_SECRET"
        "POLYGON_API_KEY"
        "STRIPE_SECRET_KEY"
    )

    # Function to check if all required vars are set
    check_required_vars() {
        local missing_vars=()
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var:-}" ]]; then
                missing_vars+=("$var")
            fi
        done

        # Print missing vars if any are found
        if [[ ${#missing_vars[@]} -gt 0 ]]; then
            log_info "Missing environment variables: ${missing_vars[*]}"
        fi

        if [[ ${#missing_vars[@]} -eq 0 ]]; then
            return 0  # All vars are set
        else
            return 1  # Some vars are missing
        fi
    }

    # First check: see if all required vars are already set
    if check_required_vars; then
        log_success "All required environment variables are already set!"
        return 0
    fi

    log_info "Attempting to load from .dev file..."

    # Check if .dev file exists
    if [[ ! -f .dev ]]; then
        log_error "Error: .dev file not found!"
        log_error "Please create a .dev file with the required environment variables"
        exit 1
    fi

    # Load environment variables from .dev file
    log_info "Loading environment variables from .dev file..."
    set -a
    source .dev
    set +a

    # Second check: verify all required vars are now set after loading .dev
    if check_required_vars; then
        log_success "Loaded environment variables successfully!"
        return 0
    else
        # Build helpful error message showing what's still missing
        local still_missing=()
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var:-}" ]]; then
                still_missing+=("$var")
            fi
        done

        log_error "Error: The following required variables are still not set after loading .dev file:"
        for var in "${still_missing[@]}"; do
            log_error "  - $var"
        done
        log_error ""
        log_error "Please add the missing variables to your .dev file in the format:"
        for var in "${still_missing[@]}"; do
            log_error "  $var=your_value_here"
        done

        exit 1
    fi
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

    # Build common variable arguments, majority of Terraform variables are non-sensitive
    # and can be directly included in the environment's terraform.tfvars file, for the
    # sensitive variables, they are set as environment variables and passed in as command
    # line arguments
    var_args=(
        -var-file="../environments/$ENVIRONMENT/terraform.tfvars"
        -var="access_token_secret_key=$ACCESS_TOKEN_SECRET_KEY"
        -var="refresh_token_secret_key=$REFRESH_TOKEN_SECRET_KEY"
        -var="datadog_api_key=$DATADOG_API_KEY"
        -var="datadog_app_key=$DATADOG_APP_KEY"
        -var="datadog_site=$DATADOG_SITE"
        -var="plaid_client_id=$PLAID_CLIENT_ID"
        -var="plaid_secret=$PLAID_SECRET"
        -var="polygon_api_key=$POLYGON_API_KEY"
        -var="stripe_secret_key=$STRIPE_SECRET_KEY"
    )

    # Run the specified action
    case $ACTION in
        plan)
            log_info "Running Terraform plan..."
            terraform plan "${var_args[@]}"
            ;;
        apply)
            log_info "Running Terraform apply..."
            terraform apply "${var_args[@]}"
            ;;
        destroy)
            log_warning "Running Terraform destroy..."
            log_warning "This will destroy resources in the $ENVIRONMENT environment!"
            read -p "Are you sure? (yes/no): " -r
            if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                terraform destroy "${var_args[@]}"
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
    unset DD_HOST
    unset DATADOG_API_KEY
    unset DATADOG_APP_KEY
    unset DATADOG_SITE
    unset ACCESS_TOKEN_SECRET_KEY
    unset REFRESH_TOKEN_SECRET_KEY
    unset PLAID_CLIENT_ID
    unset PLAID_SECRET
    unset POLYGON_API_KEY
    unset STRIPE_SECRET_KEY
    log_info "Cleaned up sensitive environment variables"
}

# Main execution
main() {
    log_info "🚀 Starting deployment process..."

    # set environment variables from .env file
    set_environment_variables

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