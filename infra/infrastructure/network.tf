/*************************
 * WalterBackend Network *
 *************************/

module "network" {
  source              = "./modules/vpc_network"
  name                = "WalterBackend"
  region              = var.region
  domain              = var.domain
  vpc_cidr            = var.network_cidr
  availability_zone   = var.availability_zone
  public_subnet_cidr  = var.public_subnet_cidr
  private_subnet_cidr = var.private_subnet_cidr
}
