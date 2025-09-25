locals {
  MEDIA_ORIGIN_ID = "WalterBackend-Media-Bucket-${var.domain}"
}

resource "aws_cloudfront_distribution" "media_cdn" {
  enabled         = true
  is_ipv6_enabled = true

  origin {
    domain_name              = var.bucket_regional_domain_name
    origin_id                = local.MEDIA_ORIGIN_ID
    origin_access_control_id = var.origin_access_control_id
  }

  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = local.MEDIA_ORIGIN_ID

    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  price_class = "PriceClass_100" # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront/PriceClass.html
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

