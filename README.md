# URL Shortener - System Design Project

## Project Overview

A production-ready URL shortener service built with Flask, PostgreSQL, and Redis. This project demonstrates advanced system design concepts, scalable architecture, and modern web development practices suitable for technical interviews and portfolio showcases.

### Key Features
- **URL Shortening**: Convert long URLs to 7-character short codes using Base62 encoding
- **Custom Aliases**: Users can create branded short links with custom codes
- **Analytics**: Real-time click tracking with user metadata and geographic data
- **API Authentication**: Secure access with API keys and rate limiting
- **Caching**: Redis-based caching for high-performance URL resolution
- **Scalable Design**: Architecture ready for horizontal scaling and database sharding

### Architecture Highlights
- **Performance**: Designed for 8,000+ reads/sec and 40+ writes/sec
- **Storage**: Optimized for 120 billion URLs with proper database indexing
- **Security**: Input validation, SQL injection prevention, rate limiting
- **Reliability**: Comprehensive error handling and health monitoring
- **Deployment**: Dockerized for easy deployment and scaling

---

## Quick Start Guide

### Prerequisites
- Python 3.8+
- PostgreSQL 12+ (or SQLite for simple setup)
- Redis 6+ (optional but recommended)
- Docker (optional, for containerized deployment)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd url-shortener
pip install -r requirements.txt
```

### 2. Database Setup

**Option A: PostgreSQL (Recommended)**
```bash
# Install PostgreSQL locally
# Create database
createdb -U postgres urlshortener

# Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost:5432/urlshortener"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key"
```

**Option B: SQLite (Simple)**
```bash
# No external database needed
export DATABASE_URL="sqlite:///urlshortener.db"
export SECRET_KEY="your-secret-key"
```

### 3. Run Application
```bash
# For PostgreSQL setup
python run_local_fixed.py

# For SQLite setup  
python run_sqlite_simple.py

# For Redis-enabled version
python run_with_redis.py
```

### 4. Access Application
- **Web Interface**: http://localhost:5000
- **API Documentation**: http://localhost:5000 (scroll down)
- **Health Check**: http://localhost:5000/health

---

## System Architecture

### Technology Stack
```
Frontend:     HTML5, CSS3, JavaScript (Vanilla)
Backend:      Flask 2.3.3, Python 3.11
Database:     PostgreSQL 15 / SQLite
Cache:        Redis 7
ORM:          SQLAlchemy 3.0.5
Deployment:   Docker, Gunicorn
Testing:      Pytest, Postman Collections
```

### Architecture Diagram
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │Load Balancer│    │   Flask     │
│ (Browser/   │───▶│   (Nginx)   │───▶│Application  │
│   API)      │    │             │    │   Server    │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                          ┌───────────────────┼───────────────────┐
                          │                   │                   │
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │    Redis    │    │ PostgreSQL  │    │  Analytics  │
                   │   Cache     │    │  Primary    │    │   Engine    │
                   │ (LRU Policy)│    │  Database   │    │             │
                   └─────────────┘    └─────────────┘    └─────────────┘
```

### Database Schema
```sql
-- Users table for API key management
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- URLs table for short link storage
CREATE TABLE urls (
    id BIGSERIAL PRIMARY KEY,
    original_url TEXT NOT NULL,
    short_code VARCHAR(16) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    click_count INTEGER DEFAULT 0,
    is_custom BOOLEAN DEFAULT FALSE
);

-- Analytics table for click tracking
CREATE TABLE analytics (
    id BIGSERIAL PRIMARY KEY,
    url_id BIGINT REFERENCES urls(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    referrer TEXT,
    country VARCHAR(10)
);

-- Counters table for distributed ID generation
CREATE TABLE counters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    value BIGINT DEFAULT 100000000000
);
```

---

## Core Components

### 1. URL Encoding Algorithm (Base62)
```python
class Base62Encoder:
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    @classmethod
    def encode(cls, num):
        # Converts counter ID to 7-character Base62 string
        # Example: 100000000001 → "0000001"
        
    @classmethod  
    def decode(cls, string):
        # Converts Base62 string back to original number
        # Used for analytics and debugging
```

### 2. Caching Strategy
```python
class CacheManager:
    def __init__(self, redis_client, ttl=3600):
        # LRU eviction policy with 1-hour TTL
        
    def get_url(self, short_code):
        # Cache hit: ~1-5ms response time
        # Cache miss: Falls back to database
        
    def set_url(self, short_code, original_url):
        # Caches URL mapping for future requests
```

### 3. Rate Limiting
```python
# API Protection
@limiter.limit("10 per minute")  # URL creation
@limiter.limit("5 per hour")     # User creation
```

---

## API Reference

### Authentication
All authenticated endpoints require an API key:
```
Header: X-API-Key: your-api-key
OR
Query Parameter: ?api_key=your-api-key
```

### Core Endpoints

#### POST /api/shorten
Create a shortened URL
```json
Request:
{
    "url": "https://example.com/very/long/url",
    "custom_code": "my-brand",        // optional
    "api_key": "your-api-key",        // optional
    "expires_in_days": 365            // optional
}

Response (201):
{
    "short_url": "http://localhost:5000/abc123d",
    "short_code": "abc123d", 
    "original_url": "https://example.com/very/long/url",
    "created_at": "2024-01-15T10:30:00Z",
    "expires_at": "2025-01-15T10:30:00Z"
}
```

#### GET /{short_code}
Redirect to original URL
```
Response: 302 Found
Location: https://original-url.com
```

#### GET /api/stats/{short_code}
Get URL analytics
```json
Response (200):
{
    "url_data": {
        "id": 1,
        "original_url": "https://example.com",
        "click_count": 150,
        "created_at": "2024-01-15T10:30:00Z"
    },
    "total_clicks": 150,
    "daily_clicks": {
        "2024-01-15": 50,
        "2024-01-16": 100  
    },
    "recent_clicks": [...]
}
```

#### POST /api/user/create
Create user and get API key
```json
Request:
{
    "email": "user@example.com"    // optional
}

Response (201):
{
    "api_key": "abc123def456...",
    "email": "user@example.com",
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET /health
Health check and system status
```json
Response (200):
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "features": ["URL shortening", "Analytics", "Rate limiting"]
}
```

---

## Testing Guide

### Manual Testing
1. **Web Interface**: Visit http://localhost:5000
2. **Create Short URL**: Test with https://www.google.com
3. **Custom Codes**: Try branded links like "portfolio" or "github"
4. **API Testing**: Use provided Postman collection

### Automated Testing
```bash
# Unit tests
pytest tests/ -v

# API tests with coverage
pytest tests/ --cov=app --cov-report=html

# Load testing
python performance_test.py
```

### Performance Benchmarks
```bash
# URL Creation Performance
ab -n 1000 -c 10 -T 'application/json' -p test_data.json http://localhost:5000/api/shorten
# Target: >40 requests/second

# URL Redirection Performance  
ab -n 5000 -c 50 http://localhost:5000/short_code
# Target: >1000 requests/second
```

---

## Performance Specifications

### Capacity Planning
- **URL Storage**: 120 billion URLs (62^7 = 3.5 trillion possible combinations)
- **Write Throughput**: 40+ URLs/second
- **Read Throughput**: 8,000+ redirections/second
- **Response Time**: <100ms for cached redirections
- **Cache Hit Rate**: >80% for frequently accessed URLs

### Scalability Features
- **Database Sharding**: Counter-based partitioning ready
- **Horizontal Scaling**: Stateless application design
- **Caching**: Redis cluster support
- **Load Balancing**: Multiple server instances
- **CDN Integration**: Static asset optimization

### Monitoring Metrics
- **QPS**: Queries per second (read/write split)
- **Latency**: P50, P95, P99 response times
- **Error Rate**: 4xx/5xx HTTP responses
- **Cache Performance**: Hit/miss ratios
- **Database**: Connection pool utilization

---

## Security Features

### Input Validation
- URL format validation with regex patterns
- Custom code sanitization (alphanumeric + hyphens/underscores)
- SQL injection prevention via SQLAlchemy ORM
- XSS protection with input escaping

### Access Control
- API key authentication (32-character random strings)
- Rate limiting per endpoint and user
- Request size limits
- CORS configuration for web APIs

### Security Headers
```python
# Recommended production headers
{
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY", 
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000"
}
```

---

## Deployment Options

### Local Development
```bash
# Simple SQLite setup
python run_sqlite_simple.py

# Full PostgreSQL + Redis setup
python run_with_redis.py
```

### Docker Deployment
```bash
# Complete stack with Docker Compose
docker-compose up -d

# Initialize database
docker-compose exec app flask init-db
```

### Production Deployment
```bash
# Using Gunicorn WSGI server
gunicorn --bind 0.0.0.0:5000 --workers 4 run:app

# With reverse proxy (Nginx)
upstream url_shortener {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;  # Multiple workers
}
```

### Cloud Deployment Options
- **AWS**: ECS + RDS + ElastiCache
- **Google Cloud**: Cloud Run + Cloud SQL + Memorystore
- **Azure**: Container Instances + Azure Database + Redis Cache
- **Heroku**: Heroku Postgres + Heroku Redis

---

## System Design Considerations

### Scalability Patterns
1. **Database Sharding**: Partition URLs by counter ranges
2. **Read Replicas**: Separate read/write database instances
3. **Caching Layers**: Multi-level caching (Redis + CDN)
4. **Microservices**: Split analytics, URL creation, and redirection

### High Availability
- **Database Replication**: Master-slave PostgreSQL setup
- **Redis Clustering**: Distributed cache with failover
- **Load Balancing**: Multiple application instances
- **Health Checks**: Automated monitoring and alerting

### Data Consistency
- **ACID Transactions**: PostgreSQL ensures data integrity
- **Cache Invalidation**: TTL-based and manual cache clearing
- **Eventual Consistency**: Analytics data can be slightly delayed
- **Backup Strategy**: Regular database backups and point-in-time recovery

---

## Configuration Management

### Environment Variables
```bash
# Required
DATABASE_URL="postgresql://user:pass@host:port/dbname"
SECRET_KEY="cryptographically-secure-random-string"
BASE_URL="https://your-domain.com"

# Optional
REDIS_URL="redis://host:port/db"
FLASK_ENV="production"
RATE_LIMIT_STORAGE_URL="redis://host:port/db"
```

### Application Settings
```python
class Config:
    SHORT_URL_LENGTH = 7                # Base62 encoded length
    CUSTOM_URL_MAX_LENGTH = 16          # User-defined codes
    URL_EXPIRY_DAYS = 365              # Default expiration
    CACHE_TTL = 3600                   # Redis cache timeout
    RATE_LIMIT_PER_MINUTE = 10         # API rate limiting
```

---

## Troubleshooting Guide

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL service
net start postgresql-x64-15  # Windows
sudo service postgresql start  # Linux

# Verify database exists
psql -U postgres -l | grep urlshortener

# Test connection
python -c "import psycopg2; psycopg2.connect('postgresql://postgres:password@localhost/urlshortener')"
```

#### Redis Connection Issues
```bash
# Check Redis service
redis-cli ping  # Should return PONG

# Start Redis with Docker
docker run --name redis-url-shortener -p 6379:6379 -d redis:7-alpine

# App works without Redis (performance impact only)
```

#### Performance Issues
```bash
# Check database indexes
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

# Monitor Redis cache hit rate
redis-cli info stats | grep keyspace_hits
```

### Error Codes
- **400 Bad Request**: Invalid URL format or missing required fields
- **401 Unauthorized**: Invalid or missing API key
- **409 Conflict**: Custom short code already exists
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Database or server error

---

## Learning Resources

### System Design Concepts Demonstrated
1. **URL Shortening Algorithms**: Base62 encoding, counter-based IDs
2. **Database Design**: Indexing, relationships, query optimization
3. **Caching Strategies**: Cache-aside pattern, TTL management
4. **API Design**: RESTful principles, authentication, rate limiting
5. **Scalability**: Horizontal scaling, database sharding concepts
6. **Performance**: Response time optimization, throughput analysis

### Technologies and Patterns
- **Flask Framework**: Web application structure, blueprints
- **SQLAlchemy ORM**: Database abstraction, migrations
- **Redis**: In-memory caching, data structures
- **PostgreSQL**: ACID transactions, indexing, performance tuning
- **Docker**: Containerization, service orchestration
- **Testing**: Unit tests, integration tests, API testing

### Interview Topics Covered
- Design a URL shortener (common system design question)
- Database scaling and sharding strategies  
- Caching patterns and cache invalidation
- API rate limiting and security
- Performance optimization techniques
- Monitoring and observability

---

## Technical Achievements

This project demonstrates expertise in:

- Production-grade REST API with Flask
- PostgreSQL database design with optimized indexing
- Redis caching with LRU eviction policy
- Base62 encoding algorithm implementation
- System designed for 8K+ reads/sec, 40+ writes/sec
- Rate limiting and security best practices
- Real-time analytics and click tracking
- Docker containerization and deployment
- Comprehensive testing and documentation

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)  
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests before committing  
pytest tests/ -v

# Format code
black app/ tests/
flake8 app/ tests/
```

---


## Acknowledgments

- System design patterns from high-scale URL shorteners (bit.ly, TinyURL)
- Flask ecosystem and SQLAlchemy ORM documentation
- Redis caching strategies and performance optimization techniques
- PostgreSQL indexing and query optimization best practices

---

**Built for learning system design and demonstrating scalable architecture principles**

*For questions, improvements, or technical discussions, please open an issue or reach out.*