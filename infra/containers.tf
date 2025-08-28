resource "aws_ecr_repository" "walter_backend" {
  name = "walter-backend"
}

data "aws_ecr_image" "walter_backend_image" {
  repository_name = aws_ecr_repository.walter_backend.name
  image_tag       = "latest"
}


