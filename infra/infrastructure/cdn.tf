locals {
  CDN_BUCKET_NAME_PREFIX                = "walter-backend-media"
  CDN_ORIGIN_ACCESS_CONTROL_NAME_PREFIX = "WalterBackend-CDN-OriginAccessControl"
}

/*********************
 * WalterBackend CDN *
 *********************/

module "cdn" {
  source                      = "./modules/cloudfront_cdn"
  domain                      = var.domain
  bucket_regional_domain_name = module.cdn_bucket.bucket_regional_domain_name
  origin_access_control_id    = aws_cloudfront_origin_access_control.oac.id
}

module "cdn_bucket" {
  source      = "./modules/s3_bucket"
  domain      = var.domain
  name_prefix = local.CDN_BUCKET_NAME_PREFIX
  read_access_principals = [
    {
      prefix     = "*",
      principals = concat([], var.cdn_bucket_access_additional_principals)
    },
    {
      prefix = "public/logos/*"
      principals = [
        module.workflow_roles["sync_transactions"].role_arn
      ]
    }
  ]
  write_access_principals = [
    {
      prefix = "*",
      principals = concat([
        module.workflow_roles["sync_transactions"].role_arn
      ], var.cdn_bucket_access_additional_principals)
    },
    {
      prefix = "public/logos/*"
      principals = [
        module.workflow_roles["sync_transactions"].role_arn
      ]
    }
  ]
  delete_access_principals = [
    {
      prefix     = "*",
      principals = concat([], var.cdn_bucket_access_additional_principals)
    }
  ]
  cloudfront_distribution_arns = [
    module.cdn.distribution_arn
  ]
}

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "${local.CDN_ORIGIN_ACCESS_CONTROL_NAME_PREFIX}-${var.domain}"
  description                       = "OAC for CloudFront to access private S3 content."
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
  origin_access_control_origin_type = "s3"
}
