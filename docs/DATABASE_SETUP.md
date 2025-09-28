# Database Setup Guide

This guide covers setting up PostgreSQL and Redis for Orchesity IDE OSS.

## Quick Start with Docker Compose (Recommended)

The easiest way to get started is using the provided Docker Compose setup:

```bash
# Clone and start full stack
git clone https://github.com/Kolerr-Lab/Orchesity_IDE_OSS.git
cd orchesity-ide-oss
docker-compose up -d

# Check services status
docker-compose ps
```

This automatically sets up:
- PostgreSQL 15 with persistent storage
- Redis 7 with AOF persistence
- Orchesity IDE OSS with full integration
- Automatic database initialization and indexing

## Manual Setup

### PostgreSQL Setup

#### 1. Install PostgreSQL 15+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
Download from [PostgreSQL official site](https://www.postgresql.org/download/)

#### 2. Create Database and User

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE orchesity_db;
CREATE USER orchesity WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE orchesity_db TO orchesity;

-- Grant schema permissions
\c orchesity_db
GRANT ALL ON SCHEMA public TO orchesity;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO orchesity;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO orchesity;

\q
```

#### 3. Configure Environment

Add to your `.env` file:
```env
DATABASE_URL=postgresql://orchesity:your_secure_password@localhost:5432/orchesity_db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### Redis Setup

#### 1. Install Redis 7+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
Download from [Redis official site](https://redis.io/download/) or use WSL

#### 2. Configure Redis

Edit `/etc/redis/redis.conf` (Linux) or `/usr/local/etc/redis.conf` (macOS):

```conf
# Enable AOF persistence
appendonly yes
appendfsync everysec

# Set memory policy
maxmemory-policy allkeys-lru

# Security (optional)
requirepass your_redis_password
```

Restart Redis:
```bash
sudo systemctl restart redis-server  # Linux
brew services restart redis           # macOS
```

#### 3. Configure Environment

Add to your `.env` file:
```env
REDIS_URL=redis://localhost:6379
# With password: redis://:your_redis_password@localhost:6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=10
CACHE_EXPIRE_SECONDS=3600
```

## Database Initialization

When you first run Orchesity IDE OSS, it will automatically:

1. **Create Tables**: All SQLAlchemy models are created automatically
2. **Create Indexes**: Performance indexes are added for common queries
3. **Initialize Cache**: Redis connection is established and tested

### Manual Initialization

If you need to manually initialize the database:

```python
from src.database.database import create_tables, init_db
import asyncio

async def setup_db():
    await init_db()
    await create_tables()
    print("Database initialized successfully")

# Run initialization
asyncio.run(setup_db())
```

## Monitoring and Maintenance

### Database Health

Check database status:
```bash
# PostgreSQL status
sudo systemctl status postgresql

# Check connections
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
sudo -u postgres psql -d orchesity_db -c "SELECT pg_size_pretty(pg_database_size('orchesity_db'));"
```

### Redis Health

Check Redis status:
```bash
# Redis status
redis-cli ping
# Should return: PONG

# Memory usage
redis-cli info memory

# Cache statistics
redis-cli info stats
```

### Application Health

Use the built-in health endpoints:
```bash
# Overall health
curl http://localhost:8000/api/health

# Database statistics
curl http://localhost:8000/api/db/stats

# Cache statistics  
curl http://localhost:8000/api/db/cache/stats
```

## Performance Tuning

### PostgreSQL Optimization

Add to `postgresql.conf`:
```conf
# Memory settings (adjust based on your system)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 100

# Logging (for development)
log_statement = 'mod'
log_min_duration_statement = 1000
```

### Redis Optimization

Add to `redis.conf`:
```conf
# Memory optimization
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence optimization
save 900 1
save 300 10
save 60 10000

# Network optimization
tcp-keepalive 300
timeout 0
```

## Backup and Recovery

### PostgreSQL Backup

```bash
# Create backup
pg_dump -h localhost -U orchesity -d orchesity_db > backup.sql

# Restore backup
psql -h localhost -U orchesity -d orchesity_db < backup.sql
```

### Redis Backup

```bash
# Redis automatically creates dump.rdb
# To create immediate backup:
redis-cli BGSAVE

# Copy the dump file
cp /var/lib/redis/dump.rdb /path/to/backup/
```

## Troubleshooting

### Common Database Issues

1. **Connection refused**
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql
   
   # Check port availability
   sudo netstat -tlnp | grep 5432
   ```

2. **Permission denied**
   ```sql
   -- Re-grant permissions
   GRANT ALL PRIVILEGES ON DATABASE orchesity_db TO orchesity;
   GRANT ALL ON SCHEMA public TO orchesity;
   ```

3. **Too many connections**
   ```sql
   -- Check current connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Kill idle connections
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';
   ```

### Common Redis Issues

1. **Redis not available**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Check Redis logs
   tail -f /var/log/redis/redis-server.log
   ```

2. **Memory issues**
   ```bash
   # Check memory usage
   redis-cli info memory
   
   # Clear cache if needed
   redis-cli flushall
   ```

3. **Performance issues**
   ```bash
   # Monitor Redis performance
   redis-cli --latency-history
   
   # Check slow queries
   redis-cli slowlog get 10
   ```

## Docker Troubleshooting

### Container Issues

```bash
# Check container logs
docker-compose logs postgres
docker-compose logs redis
docker-compose logs orchesity-ide-oss

# Restart services
docker-compose restart postgres redis

# Reset everything (WARNING: destroys data)
docker-compose down -v
docker-compose up -d
```

### Volume Issues

```bash
# Check volumes
docker volume ls

# Inspect volume
docker volume inspect orchesity-ide-oss_postgres_data

# Backup volume
docker run --rm -v orchesity-ide-oss_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz -C /data .
```

## Environment Examples

### Development (.env.development)
```env
# Development configuration
DATABASE_URL=postgresql://orchesity:orchesity@localhost:5432/orchesity_dev
DATABASE_ECHO=true
REDIS_URL=redis://localhost:6379/1
CACHE_EXPIRE_SECONDS=600
LOG_LEVEL=DEBUG
```

### Production (.env.production)
```env
# Production configuration
DATABASE_URL=postgresql://orchesity:secure_password@db.example.com:5432/orchesity_prod
DATABASE_ECHO=false
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
REDIS_URL=redis://:redis_password@cache.example.com:6379/0
CACHE_EXPIRE_SECONDS=3600
LOG_LEVEL=INFO
```

### Testing (.env.testing)
```env
# Testing configuration
DATABASE_URL=postgresql://orchesity:test@localhost:5432/orchesity_test
REDIS_URL=redis://localhost:6379/2
CACHE_EXPIRE_SECONDS=60
LOG_LEVEL=WARNING
```