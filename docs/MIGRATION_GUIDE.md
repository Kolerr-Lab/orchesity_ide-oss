# Migration Guide: Upgrading to Orchesity IDE OSS v2

This guide helps existing users migrate from Orchesity IDE OSS v1 to v2, which introduces Redis caching, PostgreSQL database persistence, and the Dynamic Weight Algorithm (DWA) for intelligent provider selection.

## Overview of Changes

### Major New Features

- **Redis Caching**: High-performance response caching and session storage
- **PostgreSQL Database**: Persistent storage for requests, metrics, and sessions
- **Dynamic Weight Algorithm (DWA)**: Intelligent provider selection based on performance metrics
- **Enhanced Health Monitoring**: Comprehensive system status with detailed metrics
- **Database Analytics**: Request logging, provider performance tracking, workflow management

### Breaking Changes

1. **Environment Variables**: New required variables for database and cache configuration
2. **Docker Compose**: Additional services (PostgreSQL, Redis) required
3. **API Responses**: Enhanced response format with additional metadata
4. **Configuration**: New settings for DWA strategy and database connections

## Pre-Migration Checklist

Before starting the migration:

- [ ] **Backup existing data** (if you have any custom configurations)
- [ ] **Review system requirements** (ensure sufficient resources for PostgreSQL + Redis)
- [ ] **Update Docker and Docker Compose** to latest versions
- [ ] **Prepare API keys** for all LLM providers you plan to use
- [ ] **Plan downtime** for the migration process

## Step-by-Step Migration

### Step 1: Update Repository

```bash
# Pull latest changes
git pull origin main

# Or clone fresh repository
git clone https://github.com/your-org/orchesity_ide-oss.git
cd orchesity_ide-oss
```

### Step 2: Environment Configuration

Create or update your `.env` file with new required variables:

#### Required New Variables

```bash
# Database Configuration (NEW)
DATABASE_URL=postgresql+asyncpg://orchesity_user:secure_password@postgres:5432/orchesity_db
DATABASE_ECHO=false

# Redis Configuration (NEW)
REDIS_URL=redis://redis:6379/0
REDIS_DB=0
CACHE_EXPIRE_SECONDS=3600

# DWA Configuration (NEW)
DWA_ROUTING_STRATEGY=load_balanced
```

#### Updated Variables

```bash
# Existing LLM Provider Keys (unchanged)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GEMINI_API_KEY=your-gemini-key
GROK_API_KEY=your-grok-key

# Application Settings (updated)
DEBUG=false
LOG_LEVEL=INFO
```

#### Complete .env Template

```bash
# LLM Provider API Keys
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GEMINI_API_KEY=your-gemini-key
GROK_API_KEY=your-grok-key

# Database Configuration
DATABASE_URL=postgresql+asyncpg://orchesity_user:secure_password@postgres:5432/orchesity_db
DATABASE_ECHO=false
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_DB=0
CACHE_EXPIRE_SECONDS=3600
REDIS_POOL_SIZE=10
REDIS_MAX_CONNECTIONS=20

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
DWA_ROUTING_STRATEGY=load_balanced

# Security (Production)
SECRET_KEY=your-super-secure-secret-key-here
```

### Step 3: Stop Existing Services

```bash
# Stop v1 services
docker-compose down

# Clean up old containers (optional)
docker system prune -f
```

### Step 4: Database Setup

The new version requires PostgreSQL. The database will be automatically initialized on first startup.

```bash
# Start PostgreSQL service first
docker-compose up -d postgres

# Wait for database to be ready
docker-compose logs postgres | grep "database system is ready"

# Verify database connection
docker exec orchesity-postgres-1 psql -U orchesity_user -d orchesity_db -c "SELECT version();"
```

### Step 5: Redis Setup

```bash
# Start Redis service
docker-compose up -d redis

# Verify Redis connection
docker exec orchesity-redis-1 redis-cli ping
```

### Step 6: Start Application

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# Verify application health
curl http://localhost:8000/api/health
```

Expected health response:
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

## Configuration Changes

### DWA Strategy Options

Configure the DWA routing strategy in your `.env` file:

```bash
# Available strategies:
DWA_ROUTING_STRATEGY=load_balanced    # Default: Balanced performance
DWA_ROUTING_STRATEGY=round_robin      # Equal rotation
DWA_ROUTING_STRATEGY=random           # Random selection
DWA_ROUTING_STRATEGY=priority         # Priority-based selection
```

### Database Connection Tuning

For production deployments, tune database connections:

```bash
# Connection Pool Settings
DB_POOL_SIZE=20              # Number of persistent connections
DB_MAX_OVERFLOW=0            # Additional connections allowed
DB_POOL_TIMEOUT=30           # Timeout for getting connection
DB_POOL_RECYCLE=3600         # Recycle connections after 1 hour
```

### Redis Configuration

Optimize Redis for your workload:

```bash
# Redis Settings
REDIS_DB=0                   # Redis database number
CACHE_EXPIRE_SECONDS=3600    # Default cache expiration (1 hour)
REDIS_POOL_SIZE=10           # Connection pool size
REDIS_MAX_CONNECTIONS=20     # Maximum connections
```

## API Changes

### New Endpoints

v2 introduces several new API endpoints:

#### DWA Management
- `GET /api/llm/dwa/stats` - DWA performance statistics
- `POST /api/llm/dwa/reset` - Reset DWA metrics
- `GET /api/llm/dwa/best-provider` - Get best performing provider

#### Database & Cache Management
- `GET /api/db/stats` - Database statistics
- `GET /api/db/cache/stats` - Cache performance metrics
- `DELETE /api/db/cache/clear` - Clear cache data
- `GET /api/db/requests/recent` - Recent request history

#### Enhanced Health Checks
- `GET /api/health` - Comprehensive system health (enhanced)

### Response Format Changes

#### v1 Response Format
```json
{
  "request_id": "req_1698765432123",
  "results": [
    {
      "provider": "openai",
      "response": "Response text...",
      "response_time": 1.23
    }
  ]
}
```

#### v2 Response Format (Enhanced)
```json
{
  "request_id": "req_1698765432123",
  "results": [
    {
      "provider": "openai",
      "response": "Response text...",
      "response_time": 1.23,
      "tokens_used": 234,
      "cached": false,
      "dwa_score": 0.95
    }
  ],
  "metadata": {
    "total_response_time": 1.35,
    "cached_response": false,
    "dwa_selection_reason": "best_performance",
    "database_logged": true
  }
}
```

## Data Migration

### No Data Loss

v2 is designed for new installations. If you have custom data from v1:

1. **API Keys**: Simply copy your existing `.env` file and add new variables
2. **Custom Configurations**: Review and update configuration files
3. **Logs**: v1 logs remain accessible; v2 creates new log structure

### Historical Data

v2 starts with a clean database. If you need to preserve historical data:

1. **Export v1 data** (if applicable)
2. **Use database import tools** to migrate specific data
3. **Contact support** for migration assistance

## Testing Migration

### Verification Steps

1. **Health Check**
```bash
curl http://localhost:8000/api/health | jq '.'
```

2. **Test LLM Request**
```bash
curl -X POST http://localhost:8000/api/llm/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test prompt",
    "providers": ["openai"],
    "temperature": 0.7
  }'
```

3. **Check DWA Stats**
```bash
curl http://localhost:8000/api/llm/dwa/stats | jq '.'
```

4. **Verify Database Connection**
```bash
curl http://localhost:8000/api/db/stats | jq '.'
```

5. **Test Cache Performance**
```bash
curl http://localhost:8000/api/db/cache/stats | jq '.'
```

### Performance Testing

```bash
# Simple load test
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/llm/orchestrate \
    -H "Content-Type: application/json" \
    -d '{"prompt":"Test '$i'","providers":["openai"]}' &
done
wait

# Check performance metrics
curl http://localhost:8000/api/llm/dwa/stats | jq '.provider_stats'
```

## Troubleshooting

### Common Migration Issues

#### 1. Database Connection Errors

**Symptom**: Application fails to start with database connection errors

**Solution**:
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify database credentials
docker exec orchesity-postgres-1 psql -U orchesity_user -d orchesity_db -c "SELECT 1;"

# Reset database
docker-compose down postgres
docker volume rm orchesity_ide-oss_postgres_data
docker-compose up -d postgres
```

#### 2. Redis Connection Issues

**Symptom**: Cache operations fail or timeout

**Solution**:
```bash
# Check Redis status
docker-compose logs redis

# Test Redis connection
docker exec orchesity-redis-1 redis-cli ping

# Clear Redis data
docker exec orchesity-redis-1 redis-cli FLUSHALL
```

#### 3. DWA Not Working

**Symptom**: Provider selection seems random or ineffective

**Solution**:
```bash
# Check DWA configuration
curl http://localhost:8000/api/llm/dwa/stats

# Reset DWA metrics
curl -X POST http://localhost:8000/api/llm/dwa/reset

# Verify provider configuration
curl http://localhost:8000/api/llm/providers
```

#### 4. Missing Environment Variables

**Symptom**: Application fails with configuration errors

**Solution**:
```bash
# Check current environment
docker exec orchesity-api-1 env | grep -E "(DATABASE|REDIS|DWA)"

# Verify .env file
cat .env | grep -E "(DATABASE|REDIS|DWA)"

# Restart with updated configuration
docker-compose down
docker-compose up -d
```

### Performance Issues

#### High Memory Usage

```bash
# Monitor container resource usage
docker stats

# Check Redis memory usage
docker exec orchesity-redis-1 redis-cli INFO memory

# Optimize cache expiration
# Update CACHE_EXPIRE_SECONDS in .env file
```

#### Slow Database Queries

```bash
# Connect to database
docker exec -it orchesity-postgres-1 psql -U orchesity_user -d orchesity_db

# Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

# Optimize connection pool
# Update DB_POOL_SIZE in .env file
```

## Rollback Plan

If migration fails, you can rollback to v1:

### Rollback Steps

1. **Stop v2 services**
```bash
docker-compose down
```

2. **Checkout v1 code**
```bash
git checkout v1-tag  # Replace with actual v1 tag
```

3. **Use v1 configuration**
```bash
# Remove v2-specific variables from .env
# Keep only LLM provider keys and basic settings
```

4. **Start v1 services**
```bash
docker-compose up -d
```

### Data Preservation

v2 database and cache data will remain in Docker volumes:
- `orchesity_ide-oss_postgres_data`
- `orchesity_ide-oss_redis_data`

You can remove these volumes if not needed:
```bash
docker volume rm orchesity_ide-oss_postgres_data orchesity_ide-oss_redis_data
```

## Production Deployment

### Environment-Specific Configurations

#### Development
```bash
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_ECHO=true
CACHE_EXPIRE_SECONDS=300
```

#### Staging
```bash
DEBUG=false
LOG_LEVEL=INFO
DATABASE_ECHO=false
CACHE_EXPIRE_SECONDS=1800
```

#### Production
```bash
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_ECHO=false
CACHE_EXPIRE_SECONDS=3600
DB_POOL_SIZE=50
REDIS_MAX_CONNECTIONS=100
```

### Security Considerations

1. **Change Default Passwords**
```bash
# Update in docker-compose.yml
POSTGRES_PASSWORD=your-secure-password
```

2. **Use Secrets Management**
```bash
# Use Docker secrets or external secret management
echo "secure_password" | docker secret create db_password -
```

3. **Network Security**
```bash
# Restrict database/cache access to internal network only
# Configure firewall rules
# Use VPN for administrative access
```

### Monitoring Setup

1. **Application Monitoring**
```bash
# Set up Prometheus metrics collection
# Configure Grafana dashboards
# Set up alerting rules
```

2. **Database Monitoring**
```bash
# Monitor PostgreSQL performance
# Set up backup procedures
# Configure connection monitoring
```

3. **Cache Monitoring**
```bash
# Monitor Redis performance
# Set up memory usage alerts
# Configure persistence settings
```

## Support and Resources

### Getting Help

- **Documentation**: Check `docs/` directory for detailed guides
- **GitHub Issues**: Report problems on the repository
- **Community**: Join discussions and get community support

### Useful Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Migration Checklist

Complete migration checklist:

- [ ] Repository updated to v2
- [ ] Environment variables configured
- [ ] PostgreSQL service running
- [ ] Redis service running
- [ ] Application health check passing
- [ ] DWA stats available
- [ ] Database stats accessible
- [ ] Cache performance verified
- [ ] API endpoints tested
- [ ] Performance validated
- [ ] Monitoring configured
- [ ] Backup procedures implemented
- [ ] Documentation reviewed
- [ ] Team training completed

## Post-Migration Tasks

### Optimization

1. **Fine-tune DWA Strategy**
```bash
# Monitor provider performance
curl http://localhost:8000/api/llm/dwa/stats

# Adjust strategy based on usage patterns
# Update DWA_ROUTING_STRATEGY in .env
```

2. **Database Performance**
```bash
# Monitor query performance
# Adjust connection pool settings
# Implement query optimization
```

3. **Cache Optimization**
```bash
# Monitor cache hit rates
# Adjust expiration times
# Implement cache warming strategies
```

### Maintenance

1. **Regular Backups**
```bash
# Set up automated database backups
# Configure backup retention policies
# Test restore procedures
```

2. **Log Management**
```bash
# Configure log rotation
# Set up log aggregation
# Implement log analysis
```

3. **Updates**
```bash
# Subscribe to release notifications
# Plan regular update cycles
# Test updates in staging environment
```

Congratulations! You have successfully migrated to Orchesity IDE OSS v2. The new features will provide enhanced performance, reliability, and intelligence for your multi-LLM orchestration needs.