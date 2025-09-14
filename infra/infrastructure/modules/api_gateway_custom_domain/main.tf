locals {
  subdomain = var.domain == "prod" ? "api" : "${var.domain}-api"
  fqdn      = "${local.subdomain}.${var.base_domain}"
}

resource "aws_acm_certificate" "certificate" {
  domain_name       = local.fqdn
  validation_method = "DNS"

  tags = {
    Name = "WalterBackend-API-Certificate-${var.domain}"
  }
}

resource "aws_route53_record" "certificate_validation" {
  for_each = {
    for dvo in aws_acm_certificate.certificate.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id = var.hosted_zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

resource "aws_acm_certificate_validation" "cert_validation" {
  certificate_arn         = aws_acm_certificate.certificate.arn
  validation_record_fqdns = [for record in aws_route53_record.certificate_validation : record.fqdn]
}

resource "aws_api_gateway_domain_name" "custom_domain" {
  domain_name     = local.fqdn
  certificate_arn = aws_acm_certificate_validation.cert_validation.certificate_arn
}

resource "aws_api_gateway_base_path_mapping" "mapping" {
  api_id      = var.api_id
  stage_name  = var.stage_name
  domain_name = aws_api_gateway_domain_name.custom_domain.domain_name
}

resource "aws_route53_record" "dns_record" {
  zone_id = var.hosted_zone_id
  name    = local.fqdn
  type    = "A"

  alias {
    name                   = aws_api_gateway_domain_name.custom_domain.cloudfront_domain_name
    zone_id                = aws_api_gateway_domain_name.custom_domain.cloudfront_zone_id
    evaluate_target_health = false
  }
}
