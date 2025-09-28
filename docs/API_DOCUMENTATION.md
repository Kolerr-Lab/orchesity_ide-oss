# API Documentation - New Endpoints

This document covers the new API endpoints added in Orchesity IDE OSS v2.

## Dynamic Weight Algorithm (DWA) Endpoints

### GET `/api/llm/dwa/stats`

Get comprehensive DWA statistics and provider metrics.

**Response:**
```json
{
  "provider_stats": {
    "openai": {
      "accuracy": 0.95,
      "speed": 1.2,
      "cost": 0.002,
      "availability": 1.0,
      "consecutive_failures": 0,
      "last_success_time": 1698765432.123,
      "last_error": null,
      "weight": 1.25
    },
    "anthropic": {
      "accuracy": 0.92,
      "speed": 1.8,
      "cost": 0.003,
      "availability": 0.98,
      "consecutive_failures": 1,
      "last_success_time": 1698765400.456,
      "last_error": "Rate limit exceeded",
      "weight": 0.85
    }
  },
  "selection_policy": "weighted_composite",
  "routing_strategy": "load_balanced",
  "active_providers": 2,
  "total_providers": 4
}
```

**Usage:**
```bash
curl http://localhost:8000/api/llm/dwa/stats
```

### POST `/api/llm/dwa/reset`

Reset DWA metrics for specific provider or all providers.

**Parameters:**
- `provider` (optional): Provider name to reset ("openai", "anthropic", etc.)

**Request:**
```bash
# Reset all providers
curl -X POST http://localhost:8000/api/llm/dwa/reset

# Reset specific provider
curl -X POST "http://localhost:8000/api/llm/dwa/reset?provider=openai"
```

**Response:**
```json
{
  "message": "Reset DWA metrics for all providers",
  "provider": null
}
```

### GET `/api/llm/dwa/best-provider`

Get the current best provider according to DWA selection algorithm.

**Response:**
```json
{
  "best_provider": "openai",
  "accuracy": 0.95,
  "speed": 1.2,
  "availability": 1.0,
  "consecutive_failures": 0
}
```

**Usage:**
```bash
curl http://localhost:8000/api/llm/dwa/best-provider
```

## Database & Cache Management Endpoints

### GET `/api/db/stats`

Get comprehensive database statistics and cache performance metrics.

**Response:**
```json
{
  "total_requests": 1547,
  "active_sessions": 23,
  "total_workflows": 45,
  "cache_hit_rate": 0.67,
  "average_response_time": 1.35,
  "provider_health": {
    "openai": true,
    "anthropic": true,
    "gemini": false,
    "grok": true
  }
}
```

### GET `/api/db/cache/stats`

Get detailed Redis cache statistics.

**Response:**
```json
{
  "connected_clients": 3,
  "used_memory": 15728640,
  "used_memory_human": "15.0M",
  "keyspace_hits": 2847,
  "keyspace_misses": 1203,
  "total_commands_processed": 8934,
  "is_connected": true
}
```

### DELETE `/api/db/cache/clear`

Clear all cache data.

**Response:**
```json
{
  "message": "Cleared 156 cache entries",
  "cleared_count": 156
}
```

### DELETE `/api/db/cache/clear/{pattern}`

Clear cache entries matching specific pattern.

**Parameters:**
- `pattern`: Redis key pattern (e.g., "llm_response:*", "session:*")

**Request:**
```bash
# Clear all LLM response cache
curl -X DELETE http://localhost:8000/api/db/cache/clear/llm_response:*

# Clear specific session cache
curl -X DELETE http://localhost:8000/api/db/cache/clear/session:user123
```

**Response:**
```json
{
  "message": "Cleared 45 cache entries matching 'llm_response:*'",
  "pattern": "llm_response:*",
  "cleared_count": 45
}
```

### GET `/api/db/requests/recent`

Get recent orchestration requests with pagination.

**Parameters:**
- `limit` (optional): Number of requests to return (default: 50)
- `session_id` (optional): Filter by specific session

**Response:**
```json
[
  {
    "id": 123,
    "request_id": "req_1698765432123",
    "prompt": "Explain quantum computing",
    "providers": ["openai", "anthropic"],
    "status": "completed",
    "created_at": "2024-01-15T10:30:45Z",
    "total_response_time": 2.35,
    "tokens_used": 234,
    "results": [
      {
        "provider": "openai",
        "response": "Quantum computing is...",
        "response_time": 1.2,
        "tokens_used": 234
      }
    ],
    "errors": []
  }
]
```

### GET `/api/db/provider-metrics`

Get detailed provider performance metrics from database.

**Response:**
```json
[
  {
    "provider": "openai",
    "model": "gpt-4",
    "total_requests": 1247,
    "success_rate": 0.96,
    "average_response_time": 1.23,
    "total_tokens_used": 234567,
    "estimated_cost": 15.67,
    "is_healthy": true,
    "consecutive_failures": 0,
    "last_updated": "2024-01-15T10:30:45Z"
  }
]
```

## Enhanced Health Endpoints

### GET `/api/health`

Enhanced health check with DWA and database status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45Z",
  "version": "2.0.0",
  "services": {
    "cpu": {
      "status": "healthy",
      "usage_percent": 15.3
    },
    "memory": {
      "status": "healthy", 
      "usage_percent": 45.2,
      "available_mb": 8192
    },
    "dwa": {
      "status": "healthy",
      "active_providers": 3,
      "total_providers": 4,
      "selection_policy": "weighted_composite"
    },
    "database": {
      "status": "healthy",
      "connection_pool": {
        "active": 5,
        "idle": 3
      }
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 0.67,
      "memory_usage": "15.0M"
    },
    "llm_providers": [
      {
        "provider": "openai",
        "configured": true,
        "status": "available"
      }
    ]
  }
}
```

## Authentication & Authorization

Currently, all endpoints are public. In production deployments, consider:

1. **API Key Authentication**
   ```http
   Authorization: Bearer your-api-key
   ```

2. **Rate Limiting**
   - Implemented per endpoint
   - Configurable limits based on usage patterns

3. **IP Whitelisting**
   - Restrict access to management endpoints
   - Allow monitoring tools access

## Error Responses

All endpoints use consistent error response format:

```json
{
  "detail": "Error message description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:45Z",
  "request_id": "req_1698765432123"
}
```

### Common HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error
- `503` - Service Unavailable (database/cache connection issues)

## Usage Examples

### Monitor System Health

```bash
#!/bin/bash
# health-check.sh

# Check overall health
health=$(curl -s http://localhost:8000/api/health | jq -r '.status')
echo "System health: $health"

# Check DWA performance
best_provider=$(curl -s http://localhost:8000/api/llm/dwa/best-provider | jq -r '.best_provider')
echo "Best provider: $best_provider"

# Check cache performance
hit_rate=$(curl -s http://localhost:8000/api/db/cache/stats | jq -r '.keyspace_hits / (.keyspace_hits + .keyspace_misses)')
echo "Cache hit rate: $hit_rate"
```

### Clear Cache on Deployment

```bash
#!/bin/bash
# deployment-cache-clear.sh

echo "Clearing deployment-related cache..."

# Clear all LLM response cache (force fresh responses)
curl -X DELETE http://localhost:8000/api/db/cache/clear/llm_response:*

# Clear workflow cache
curl -X DELETE http://localhost:8000/api/db/cache/clear/workflow_result:*

echo "Cache cleared successfully"
```

### Monitor Provider Performance

```python
import requests
import json

def monitor_providers():
    """Monitor and alert on provider performance"""
    
    # Get DWA stats
    response = requests.get('http://localhost:8000/api/llm/dwa/stats')
    stats = response.json()
    
    for provider, metrics in stats['provider_stats'].items():
        # Alert on high failure rate
        if metrics['consecutive_failures'] > 3:
            print(f"ALERT: {provider} has {metrics['consecutive_failures']} consecutive failures")
        
        # Alert on poor performance
        if metrics['accuracy'] < 0.8:
            print(f"WARNING: {provider} accuracy is {metrics['accuracy']}")
        
        # Alert on high latency
        if metrics['speed'] > 5.0:
            print(f"WARNING: {provider} response time is {metrics['speed']}s")

if __name__ == "__main__":
    monitor_providers()
```

### Custom Weighting Strategy

```python
import requests

def apply_cost_optimized_strategy():
    """Apply cost-optimized weighting via API"""
    
    # This would typically be done through configuration
    # or a custom endpoint for strategy updates
    
    # Get current stats
    response = requests.get('http://localhost:8000/api/llm/dwa/stats')
    stats = response.json()
    
    # Find lowest cost provider with good availability
    best_cost_provider = min(
        stats['provider_stats'].items(),
        key=lambda x: (x[1]['cost'], -x[1]['availability'])
    )
    
    print(f"Most cost-effective provider: {best_cost_provider[0]}")
    print(f"Cost: ${best_cost_provider[1]['cost']}")
    print(f"Availability: {best_cost_provider[1]['availability']}")
```

## WebSocket Support (Planned)

Future versions will include WebSocket endpoints for real-time monitoring:

```javascript
// Real-time DWA stats
const ws = new WebSocket('ws://localhost:8000/ws/dwa/stats');
ws.onmessage = (event) => {
    const stats = JSON.parse(event.data);
    updateDashboard(stats);
};

// Real-time cache metrics
const cacheWs = new WebSocket('ws://localhost:8000/ws/cache/stats');
cacheWs.onmessage = (event) => {
    const metrics = JSON.parse(event.data);
    updateCacheMetrics(metrics);
};
```

## Rate Limiting

Default rate limits (configurable):

- **Health endpoints**: 60 requests/minute
- **Stats endpoints**: 30 requests/minute  
- **Management endpoints**: 10 requests/minute
- **Orchestration endpoints**: 100 requests/minute

## OpenAPI/Swagger Documentation

Full interactive API documentation available at:
- **Development**: http://localhost:8000/docs
- **Alternative UI**: http://localhost:8000/redoc

The OpenAPI specification includes:
- Complete request/response schemas
- Interactive testing interface
- Authentication requirements
- Rate limiting information
- Example requests and responses