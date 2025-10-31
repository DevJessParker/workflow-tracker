# Pinata Code - Backend (FastAPI)

This directory contains the FastAPI Python backend for the Pinata Code SaaS platform.

## Overview

The backend provides a RESTful API for:
- User authentication and authorization (Clerk.dev integration)
- Organization and team management
- Repository management and Git integration
- Scan orchestration and background jobs (Celery)
- Subscription billing (Stripe integration)
- Usage tracking and quota enforcement

## Tech Stack

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Background Jobs**: Celery + Redis
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Storage**: S3/MinIO
- **Auth**: Clerk.dev
- **Payments**: Stripe

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── v1/
│   │   │   ├── auth.py
│   │   │   ├── organizations.py
│   │   │   ├── repositories.py
│   │   │   ├── scans.py
│   │   │   └── webhooks.py
│   │   └── deps.py       # Dependencies (auth, db)
│   ├── core/             # Core functionality
│   │   ├── config.py     # Settings
│   │   ├── security.py   # Auth helpers
│   │   └── database.py   # DB connection
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── repository.py
│   │   └── scan.py
│   ├── schemas/          # Pydantic schemas
│   │   ├── user.py
│   │   ├── scan.py
│   │   └── repository.py
│   ├── services/         # Business logic
│   │   ├── scan_service.py
│   │   ├── cache_service.py
│   │   └── storage_service.py
│   ├── tasks/            # Celery tasks
│   │   ├── scan_tasks.py
│   │   └── export_tasks.py
│   └── main.py           # FastAPI app
├── tests/                # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/              # Database migrations
├── Dockerfile
├── Dockerfile.dev
├── pyproject.toml        # Poetry dependencies
└── pytest.ini
```

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry
- Docker (for local development)
- PostgreSQL 15
- Redis 7

### Installation

```bash
# Install dependencies
cd backend
poetry install

# Copy environment variables
cp ../.env.example ../.env
# Edit .env with your configuration

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn app.main:app --reload
```

### With Docker

```bash
# From project root
cd infrastructure/docker
docker-compose up backend
```

## Development

### Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Add users table"

# Apply migrations
poetry run alembic upgrade head

# Rollback last migration
poetry run alembic downgrade -1
```

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html

# Specific test file
poetry run pytest tests/unit/test_scan_service.py -v

# Integration tests only
poetry run pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
poetry run black app/
poetry run isort app/

# Lint
poetry run ruff app/

# Type checking
poetry run mypy app/
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Key Features

### 1. Authentication (Clerk.dev)

```python
from app.api.deps import get_current_user
from fastapi import Depends

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### 2. Background Scans (Celery)

```python
from app.tasks.scan_tasks import run_scan

# Start background scan
task = run_scan.delay(scan_id, repo_path, config)

# Check status
result = AsyncResult(task.id)
print(result.state)  # PENDING, PROGRESS, SUCCESS, FAILURE
```

### 3. Multi-Layer Caching

```python
# File-level cache
from app.services.cache_service import FileCacheService

cache = FileCacheService()
cached_result = await cache.get_cached_result(file_hash)

# API response cache
from fastapi_cache.decorator import cache

@router.get("/scans/{scan_id}")
@cache(expire=300)
async def get_scan(scan_id: str):
    return await db.get_scan(scan_id)
```

### 4. Quota Enforcement

```python
from app.middleware.quota_middleware import check_scan_quota

@router.post("/repositories/{id}/scans")
async def create_scan(
    repository_id: str,
    _: None = Depends(check_scan_quota)
):
    # Quota checked, proceed with scan
    pass
```

## Environment Variables

See `../.env.example` for all configuration options.

Key variables:
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/pinata_dev
REDIS_URL=redis://localhost:6379/0
CLERK_SECRET_KEY=sk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
```

## Database Schema

Key models:
- **User**: Synced from Clerk.dev
- **Organization**: Multi-tenant organization
- **OrganizationMember**: Team membership
- **Repository**: Connected repositories
- **Scan**: Scan jobs and results
- **Subscription**: Stripe subscriptions
- **UsageEvent**: Tracking for billing

## API Endpoints

### Organizations
- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations` - List user's orgs
- `GET /api/v1/organizations/{id}` - Get org details
- `PATCH /api/v1/organizations/{id}` - Update org
- `DELETE /api/v1/organizations/{id}` - Delete org

### Repositories
- `POST /api/v1/organizations/{id}/repositories` - Create repo
- `GET /api/v1/organizations/{id}/repositories` - List repos
- `GET /api/v1/repositories/{id}` - Get repo
- `PATCH /api/v1/repositories/{id}` - Update repo
- `DELETE /api/v1/repositories/{id}` - Delete repo

### Scans
- `POST /api/v1/repositories/{id}/scans` - Start scan
- `GET /api/v1/scans/{id}` - Get scan status
- `GET /api/v1/scans/{id}/results` - Get results
- `POST /api/v1/scans/{id}/cancel` - Cancel scan
- `WS /ws/scans/{id}` - WebSocket progress

### Billing
- `POST /api/v1/billing/create-checkout` - Start subscription
- `POST /api/v1/billing/portal` - Customer portal
- `POST /api/v1/webhooks/stripe` - Stripe webhooks

## Deployment

### Railway.app (Phase 1-2)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway up
```

### AWS ECS (Phase 3)

See `../../docs/DEPLOYMENT.md` for production deployment guide.

## Monitoring

- **Errors**: Sentry integration
- **APM**: Datadog (production)
- **Logs**: CloudWatch (production)

## Next Steps

1. ✅ Set up project structure
2. ⏳ Implement authentication
3. ⏳ Create core models
4. ⏳ Build API endpoints
5. ⏳ Integrate scanning engine
6. ⏳ Add Stripe billing
7. ⏳ Write tests

See `../../docs/IMPLEMENTATION_PLAN.md` for detailed roadmap.

## License

Part of Pinata Code - Proprietary Software
