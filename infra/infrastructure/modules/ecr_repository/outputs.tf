output "image_uri" {
  value       = data.aws_ecr_image.ecr_image.image_uri
  description = "The image URI of the given version."
}

output "image_digest" {
  value       = data.aws_ecr_image.ecr_image.image_digest
  description = "The image digest of the given version."
}
