# Docker Documentation

This document covers Docker containerization for Orchesity IDE OSS v2, including multi-service deployment with PostgreSQL, Redis, and the FastAPI application.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/orchesity_ide-oss.git
cd orchesity_ide-oss

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f orchesity-api
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │◄───┤     Redis       │    │   PostgreSQL    │
│   (Port 8000)   │    │   (Port 6379)   │    │   (Port 5432)   │
│                 │    │                 │    │                 │
│ • LLM Routing   │    │ • Response Cache│    │ • Request Log   │
│ • DWA Engine    │    │ • Session Store │    │ • Metrics Store │
│ • API Endpoints │    │ • Temp Storage  │    │ • User Sessions │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Docker Compose Configuration

### Services Overview

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `orchesity-api` | Built from Dockerfile | 8000 | Main FastAPI application |
| `postgres` | postgres:15-alpine | 5432 | Primary database |
| `redis` | redis:7-alpine | 6379 | Caching and session storage |

### Environment Variables

#### Required Variables

Create `.env` file in project root:

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GEMINI_API_KEY=your-gemini-key
GROK_API_KEY=your-grok-key

# Database Configuration
DATABASE_URL=postgresql+asyncpg://orchesity_user:secure_password@postgres:5432/orchesity_db
DATABASE_ECHO=false

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_DB=0
CACHE_EXPIRE_SECONDS=3600

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
DWA_ROUTING_STRATEGY=load_balanced

# Security (Production)
SECRET_KEY=your-super-secure-secret-key-here
```

#### Optional Variables

```bash
# Database Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis Connection Pool
REDIS_POOL_SIZE=10
REDIS_MAX_CONNECTIONS=20

# Performance Tuning
WORKER_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=65

# Monitoring
HEALTH_CHECK_INTERVAL=30
METRICS_COLLECTION_INTERVAL=60
```

### docker-compose.yml Explained

```yaml
version: '3.8'

services:
  # Main FastAPI Application
  orchesity-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://orchesity_user:secure_password@postgres:5432/orchesity_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs  # Persistent log storage

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: orchesity_db
      POSTGRES_USER: orchesity_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orchesity_user -d orchesity_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Dockerfile Explained

```dockerfile
# Multi-stage build for smaller production image
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development vs Production

### Development Setup

```bash
# Development with hot reload
docker-compose -f docker-compose.dev.yml up

# Override for development
services:
  orchesity-api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/__pycache__
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Setup

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Production overrides
services:
  orchesity-api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARNING
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Health Checks

### Container Health Checks

All services include comprehensive health checks:

```bash
# Check all service health
docker-compose ps

# Detailed health status
docker inspect orchesity-api-1 | jq '.[0].State.Health'

# View health check logs
docker logs orchesity-api-1 | grep health
```

### Application Health Endpoint

```bash
# Basic health check
curl http://localhost:8000/api/health

# Detailed health with DWA status
curl http://localhost:8000/api/health | jq '.'
```

Expected healthy response:
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "cache": {"status": "healthy"},
    "dwa": {"status": "healthy", "active_providers": 3}
  }
}
```

## Persistent Data Management

### Volumes

```bash
# List Docker volumes
docker volume ls

# Inspect volume details
docker volume inspect orchesity_ide-oss_postgres_data

# Backup database
docker exec orchesity-postgres-1 pg_dump -U orchesity_user orchesity_db > backup.sql

# Restore database
docker exec -i orchesity-postgres-1 psql -U orchesity_user orchesity_db < backup.sql
```

### Data Directories

```
orchesity_ide-oss/
├── docker-compose.yml
├── logs/                    # Application logs (mounted)
├── backups/                 # Database backups
└── data/
    ├── postgres/            # PostgreSQL data (volume)
    └── redis/               # Redis data (volume)
```

## Networking

### Internal Network

Docker Compose creates an internal network `orchesity_ide-oss_default`:

```bash
# List networks
docker network ls

# Inspect network
docker network inspect orchesity_ide-oss_default

# Service discovery
docker exec orchesity-api-1 nslookup postgres
docker exec orchesity-api-1 nslookup redis
```

### Port Mapping

- **8000**: FastAPI application (public)
- **5432**: PostgreSQL (internal only)
- **6379**: Redis (internal only)

### External Access

```bash
# Access application
curl http://localhost:8000/api/health

# Connect to database (if needed for debugging)
docker exec -it orchesity-postgres-1 psql -U orchesity_user -d orchesity_db

# Connect to Redis
docker exec -it orchesity-redis-1 redis-cli
```

## Monitoring and Logging

### Log Management

```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f orchesity-api

# View logs with timestamps
docker-compose logs -t

# Limit log output
docker-compose logs --tail=100 orchesity-api
```

### Log Rotation

Add to docker-compose.yml:

```yaml
services:
  orchesity-api:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

### Metrics Collection

```bash
# Container metrics
docker stats

# Service-specific metrics
docker stats orchesity-api-1

# Export metrics (requires monitoring stack)
curl http://localhost:8000/metrics
```

## Scaling and Load Balancing

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  orchesity-api:
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - orchesity-api
```

### Load Balancer Configuration

```nginx
# nginx.conf
upstream orchesity_backend {
    server orchesity-api-1:8000;
    server orchesity-api-2:8000;
    server orchesity-api-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://orchesity_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Considerations

### Container Security

```dockerfile
# Non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Read-only filesystem (where possible)
volumes:
  - type: tmpfs
    target: /tmp
    tmpfs:
      size: 100M

# Security scanning
docker scan orchesity-api:latest
```

### Environment Security

```bash
# Use Docker secrets in production
echo "secure_database_password" | docker secret create db_password -

# Reference in compose
services:
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
```

### Network Security

```yaml
# Custom network with isolation
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  orchesity-api:
    networks:
      - frontend
      - backend
  postgres:
    networks:
      - backend  # No external access
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test database connection
docker exec orchesity-api-1 python -c "
import asyncpg
import asyncio
async def test():
    conn = await asyncpg.connect('postgresql://orchesity_user:secure_password@postgres:5432/orchesity_db')
    print('Database connected successfully')
    await conn.close()
asyncio.run(test())
"
```

#### 2. Redis Connection Issues

```bash
# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker exec orchesity-api-1 python -c "
import redis
r = redis.Redis(host='redis', port=6379, db=0)
print(f'Redis ping: {r.ping()}')
"
```

#### 3. Application Won't Start

```bash
# Check application logs
docker-compose logs orchesity-api

# Debug container
docker run -it --rm orchesity-api /bin/bash

# Check dependencies
docker exec orchesity-api-1 pip list
```

#### 4. Health Check Failures

```bash
# Manual health check
docker exec orchesity-api-1 curl -f http://localhost:8000/api/health

# Check process status
docker exec orchesity-api-1 ps aux

# Check port binding
docker exec orchesity-api-1 netstat -tlnp | grep 8000
```

### Performance Optimization

#### Database Optimization

```sql
-- Connect to database
docker exec -it orchesity-postgres-1 psql -U orchesity_user -d orchesity_db

-- Check connection counts
SELECT count(*) FROM pg_stat_activity;

-- Monitor slow queries
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

#### Redis Optimization

```bash
# Connect to Redis
docker exec -it orchesity-redis-1 redis-cli

# Check memory usage
INFO memory

# Monitor operations
MONITOR

# Check key statistics
INFO keyspace
```

#### Application Optimization

```bash
# Check application metrics
curl http://localhost:8000/api/health | jq '.services'

# Monitor DWA performance
curl http://localhost:8000/api/llm/dwa/stats | jq '.provider_stats'

# Cache performance
curl http://localhost:8000/api/db/cache/stats | jq '.'
```

## Deployment Strategies

### Blue-Green Deployment

```bash
# Deploy new version alongside current
docker-compose -f docker-compose.blue.yml up -d

# Switch traffic after validation
docker-compose -f docker-compose.green.yml down
```

### Rolling Updates

```bash
# Update single service
docker-compose up -d --no-deps orchesity-api

# Validate before proceeding
curl http://localhost:8000/api/health

# Update remaining services
docker-compose up -d
```

### Backup Before Deployment

```bash
#!/bin/bash
# pre-deploy-backup.sh

# Backup database
docker exec orchesity-postgres-1 pg_dump -U orchesity_user orchesity_db | gzip > "backup-$(date +%Y%m%d-%H%M%S).sql.gz"

# Backup Redis (if needed)
docker exec orchesity-redis-1 redis-cli BGSAVE

# Create application snapshot
docker commit orchesity-api-1 orchesity-api:backup-$(date +%Y%m%d-%H%M%S)
```

## Monitoring Stack Integration

### Prometheus + Grafana

```yaml
# monitoring/docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
```

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Database backup strategy implemented
- [ ] Log rotation configured
- [ ] Health checks validated
- [ ] Security scanning completed
- [ ] Performance testing conducted
- [ ] Monitoring dashboards configured
- [ ] Disaster recovery plan documented
- [ ] Load balancing configured
- [ ] Auto-scaling policies defined
- [ ] Access controls implemented

## Support and Resources

### Useful Commands

```bash
# Quick status check
docker-compose ps && curl -s http://localhost:8000/api/health | jq '.status'

# Resource usage
docker stats --no-stream

# Cleanup unused resources
docker system prune -f

# Complete environment reset
docker-compose down -v && docker-compose up -d
```

### Log Locations

- **Application**: `./logs/` directory (mounted volume)
- **Database**: Docker container logs
- **Redis**: Docker container logs
- **System**: Docker daemon logs

### Configuration Files

- `docker-compose.yml`: Main service configuration
- `.env`: Environment variables
- `Dockerfile`: Application container build
- `nginx.conf`: Load balancer configuration (if used)
- `prometheus.yml`: Monitoring configuration (if used)

For additional support, refer to:
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
- [Redis Docker Documentation](https://hub.docker.com/_/redis)
- [Docker Compose Documentation](https://docs.docker.com/compose/)