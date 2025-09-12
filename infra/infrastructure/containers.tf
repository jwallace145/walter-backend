locals {
  REPOSITORIES = {
    walter_backend : {
      name    = "walter-backend-${var.domain}"
      version = var.walter_backend_version
    }
  }
}

module "repositories" {
  source          = "./modules/ecr_repository"
  for_each        = local.REPOSITORIES
  repository_name = each.value.name
  image_version   = each.value.version
}