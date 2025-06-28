# 🚀 AI 모델 관리 시스템 - 스테이징 환경 인프라
# Terraform Infrastructure as Code for Staging Environment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "ai-model-mgmt-terraform-state"
    key    = "staging/terraform.tfstate"
    region = "ap-northeast-2"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "staging"
      Project     = "ai-model-management"
      Team        = "backend"
      Owner       = "devops@company.com"
      CostCenter  = "engineering"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ai-model-mgmt"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "staging.ai-model-mgmt.com"
}

variable "api_domain_name" {
  description = "API domain name"
  type        = string
  default     = "api-staging.ai-model-mgmt.com"
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*"]
  }
  
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 2
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.1.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "${var.project_name}-${var.environment}-public-${count.index + 1}"
    Type = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 2
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.1.1${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "${var.project_name}-${var.environment}-private-${count.index + 1}"
    Type = "private"
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = 2
  
  domain = "vpc"
  
  depends_on = [aws_internet_gateway.main]
  
  tags = {
    Name = "${var.project_name}-${var.environment}-nat-eip-${count.index + 1}"
  }
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = 2
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  depends_on = [aws_internet_gateway.main]
  
  tags = {
    Name = "${var.project_name}-${var.environment}-nat-${count.index + 1}"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

resource "aws_route_table" "private" {
  count = 2
  
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-private-rt-${count.index + 1}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = 2
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 2
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-${var.environment}-alb-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Application Load Balancer"
  
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-alb-sg"
  }
}

resource "aws_security_group" "backend" {
  name_prefix = "${var.project_name}-${var.environment}-backend-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Backend services"
  
  ingress {
    description     = "Backend API"
    from_port       = 8000
    to_port         = 8002
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  ingress {
    description     = "Prometheus metrics"
    from_port       = 9090
    to_port         = 9090
    protocol        = "tcp"
    security_groups = [aws_security_group.monitoring.id]
  }
  
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.1.0.0/16"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-backend-sg"
  }
}

resource "aws_security_group" "database" {
  name_prefix = "${var.project_name}-${var.environment}-db-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Database services"
  
  ingress {
    description     = "MongoDB"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }
  
  ingress {
    description     = "Redis"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-db-sg"
  }
}

resource "aws_security_group" "monitoring" {
  name_prefix = "${var.project_name}-${var.environment}-monitoring-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Monitoring services"
  
  ingress {
    description = "Prometheus"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["10.1.0.0/16"]
  }
  
  ingress {
    description = "Grafana"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["10.1.0.0/16"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-monitoring-sg"
  }
}

# DocumentDB Subnet Group
resource "aws_docdb_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-docdb-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "${var.project_name}-${var.environment}-docdb-subnet-group"
  }
}

# DocumentDB Cluster
resource "aws_docdb_cluster" "main" {
  cluster_identifier              = "${var.project_name}-${var.environment}-docdb"
  engine                         = "docdb"
  engine_version                 = "5.0.0"
  master_username                = "admin"
  master_password                = var.docdb_password
  db_subnet_group_name           = aws_docdb_subnet_group.main.name
  vpc_security_group_ids         = [aws_security_group.database.id]
  backup_retention_period        = 7
  preferred_backup_window        = "03:00-04:00"
  preferred_maintenance_window   = "sun:04:00-sun:05:00"
  storage_encrypted              = true
  enabled_cloudwatch_logs_exports = ["audit", "profiler"]
  deletion_protection            = false  # Set to true for production
  
  tags = {
    Name = "${var.project_name}-${var.environment}-docdb"
  }
}

# DocumentDB Cluster Instances
resource "aws_docdb_cluster_instance" "main" {
  count              = 2
  identifier         = "${var.project_name}-${var.environment}-docdb-${count.index + 1}"
  cluster_identifier = aws_docdb_cluster.main.id
  instance_class     = "db.t3.medium"
  
  tags = {
    Name = "${var.project_name}-${var.environment}-docdb-${count.index + 1}"
  }
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-redis-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "${var.project_name}-${var.environment}-redis-subnet-group"
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.project_name}-${var.environment}-redis"
  description               = "Redis cluster for ${var.project_name} ${var.environment}"
  
  port                      = 6379
  parameter_group_name      = "default.redis7"
  node_type                = "cache.t3.micro"
  num_cache_clusters        = 2
  
  subnet_group_name         = aws_elasticache_subnet_group.main.name
  security_group_ids        = [aws_security_group.database.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = var.redis_auth_token
  
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  maintenance_window        = "sun:03:00-sun:04:00"
  snapshot_retention_limit  = 5
  snapshot_window          = "02:00-03:00"
  
  tags = {
    Name = "${var.project_name}-${var.environment}-redis"
  }
}

# IAM Role for EC2 instances
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-${var.environment}-ec2-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-role"
  }
}

# IAM Role Policy for ECR access
resource "aws_iam_role_policy" "ecr_policy" {
  name = "${var.project_name}-${var.environment}-ecr-policy"
  role = aws_iam_role.ec2_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "ec2:DescribeVolumes",
          "ec2:DescribeTags",
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "logs:CreateLogStream"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name
  
  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-profile"
  }
}

# Launch Template for Backend instances
resource "aws_launch_template" "backend" {
  name_prefix   = "${var.project_name}-${var.environment}-backend-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t3.large"
  
  vpc_security_group_ids = [aws_security_group.backend.id]
  
  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }
  
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    environment = var.environment
    project_name = var.project_name
  }))
  
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-${var.environment}-backend"
      Type = "backend"
    }
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-backend-lt"
  }
}

# Auto Scaling Group
resource "aws_autoscaling_group" "backend" {
  name                = "${var.project_name}-${var.environment}-backend-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.backend.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 300
  
  min_size         = 2
  max_size         = 6
  desired_capacity = 3
  
  launch_template {
    id      = aws_launch_template.backend.id
    version = "$Latest"
  }
  
  tag {
    key                 = "Name"
    value              = "${var.project_name}-${var.environment}-backend"
    propagate_at_launch = true
  }
  
  tag {
    key                 = "Environment"
    value              = var.environment
    propagate_at_launch = true
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id
  
  enable_deletion_protection = false  # Set to true for production
  
  tags = {
    Name = "${var.project_name}-${var.environment}-alb"
  }
}

# Target Group for Backend
resource "aws_lb_target_group" "backend" {
  name     = "${var.project_name}-${var.environment}-backend-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  
  health_check {
    enabled             = true
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/health"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-backend-tg"
  }
}

# ALB Listener (HTTP)
resource "aws_lb_listener" "backend_http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type = "redirect"
    
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# ALB Listener (HTTPS)
resource "aws_lb_listener" "backend_https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate_validation.main.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# ECR Repository
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}/backend"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Name = "${var.project_name}-backend-ecr"
  }
}

# Variables for sensitive data
variable "docdb_password" {
  description = "Password for DocumentDB master user"
  type        = string
  sensitive   = true
}

variable "redis_auth_token" {
  description = "Auth token for Redis cluster"
  type        = string
  sensitive   = true
}

# SSL Certificate
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = [var.api_domain_name]
  validation_method         = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = {
    Name = "${var.project_name}-${var.environment}-cert"
  }
}

# Route53 Zone (assuming it exists)
data "aws_route53_zone" "main" {
  name         = "ai-model-mgmt.com"
  private_zone = false
}

# Route53 Records for certificate validation
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

# Certificate validation
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
  
  timeouts {
    create = "5m"
  }
}

# Route53 Records for ALB
resource "aws_route53_record" "main" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.api_domain_name
  type    = "A"
  
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "docdb_endpoint" {
  description = "DocumentDB cluster endpoint"
  value       = aws_docdb_cluster.main.endpoint
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "domain_name" {
  description = "Domain name"
  value       = var.domain_name
}

output "api_domain_name" {
  description = "API domain name"
  value       = var.api_domain_name
}