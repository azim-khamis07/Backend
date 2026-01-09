# Security Group for ElastiCache
resource "aws_security_group" "redis" {
  name_prefix = "${replace(var.tags.Name, "-", "")}redis"
  vpc_id      = var.vpc_id
  description = "Security group for ElastiCache Redis"

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.tags.Name}-redis-sg"
  })
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.tags.Name}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.tags.Name}-redis-subnet-group"
  })
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.tags.Name}-redis"
  description                = "Redis cluster for ${var.tags.Name}"

  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.node_type
  port                 = 6379

  # For replication group: use num_node_groups instead of num_cache_nodes
  # For single node: num_node_groups = 1, replicas_per_node_group = 0 (default)
  # For multiple nodes with replication: num_node_groups = 1, replicas_per_node_group = N
  num_node_groups         = 1
  replicas_per_node_group = var.num_cache_nodes > 1 ? (var.num_cache_nodes - 1) : 0

  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false

  automatic_failover_enabled = var.num_cache_nodes > 1 ? true : false
  multi_az_enabled          = var.num_cache_nodes > 1 ? true : false

  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"

  tags = merge(var.tags, {
    Name = "${var.tags.Name}-redis"
  })
}

