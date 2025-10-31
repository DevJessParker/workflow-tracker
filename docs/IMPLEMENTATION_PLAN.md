# Pinata Code - Production SaaS Implementation Plan

## Vision
Transform Pinata Code from a standalone tool into a production-ready, multi-tenant SaaS platform with React frontend, Python backend, robust testing, and optimized performance.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (React + Next.js)                                │
│  ├─ Next.js 14 (App Router)                                │
│  ├─ TypeScript                                             │
│  ├─ Tailwind CSS + Shadcn/ui                               │
│  ├─ React Query (data fetching + caching)                  │
│  ├─ Zustand (state management)                             │
│  └─ React Flow (workflow visualization)                    │
│                                                             │
│  API Gateway (Python FastAPI)                              │
│  ├─ FastAPI 0.104+                                         │
│  ├─ Pydantic v2 (validation)                               │
│  ├─ SQLAlchemy 2.0 (ORM)                                   │
│  ├─ Alembic (migrations)                                   │
│  ├─ Redis (caching + sessions)                             │
│  └─ Celery (background jobs)                               │
│                                                             │
│  Scanning Engine (Python - KEEP EXISTING)                  │
│  ├─ Current scanning logic (minimal changes)               │
│  ├─ Multiprocessing for parallelism                        │
│  ├─ Incremental scanning (new)                             │
│  └─ Result caching (new)                                   │
│                                                             │
│  Data Layer                                                │
│  ├─ PostgreSQL 15 (primary database)                       │
│  ├─ Redis 7 (cache + queue)                                │
│  └─ S3/MinIO (scan results storage)                        │
│                                                             │
│  Infrastructure                                            │
│  ├─ Docker + Docker Compose                                │
│  ├─ GitHub Actions (CI/CD)                                 │
│  ├─ Railway.app (hosting - Phase 1)                        │
│  └─ AWS ECS (hosting - Phase 3)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure (Monorepo)

```
pinata-code/
├── frontend/                    # Next.js React app
│   ├── app/                    # Next.js 14 app router
│   │   ├── (auth)/             # Authenticated routes
│   │   │   ├── dashboard/
│   │   │   ├── repositories/
│   │   │   ├── scans/
│   │   │   └── settings/
│   │   ├── (marketing)/        # Public routes
│   │   │   ├── page.tsx        # Homepage
│   │   │   ├── pricing/
│   │   │   └── docs/
│   │   └── api/                # API routes (BFF pattern)
│   ├── components/             # React components
│   │   ├── ui/                 # Shadcn/ui components
│   │   ├── scan-results/       # Visualization components
│   │   └── dashboard/
│   ├── lib/                    # Utilities
│   │   ├── api-client.ts       # Backend API client
│   │   ├── auth.ts             # Clerk integration
│   │   └── utils.ts
│   ├── Dockerfile
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                     # FastAPI Python backend
│   ├── app/
│   │   ├── api/                # API endpoints
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── organizations.py
│   │   │   │   ├── repositories.py
│   │   │   │   ├── scans.py
│   │   │   │   └── webhooks.py
│   │   │   └── deps.py         # Dependencies (auth, db)
│   │   ├── core/               # Core functionality
│   │   │   ├── config.py       # Settings
│   │   │   ├── security.py     # Auth helpers
│   │   │   └── database.py     # DB connection
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── organization.py
│   │   │   ├── repository.py
│   │   │   └── scan.py
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── scan.py
│   │   │   └── repository.py
│   │   ├── services/           # Business logic
│   │   │   ├── scan_service.py
│   │   │   ├── cache_service.py
│   │   │   └── storage_service.py
│   │   ├── tasks/              # Celery tasks
│   │   │   ├── scan_tasks.py
│   │   │   └── export_tasks.py
│   │   └── main.py             # FastAPI app
│   ├── tests/                  # Test suite
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── alembic/                # Database migrations
│   ├── Dockerfile
│   ├── pyproject.toml          # Poetry dependencies
│   └── pytest.ini
│
├── scanner/                     # Scanning engine (EXISTING CODE)
│   ├── src/
│   │   ├── graph/              # Existing: builder, renderer
│   │   ├── scanners/           # Existing: language scanners
│   │   ├── models/             # Existing: data models
│   │   └── integrations/       # Existing: Confluence, etc.
│   ├── tests/
│   ├── setup.py
│   └── requirements.txt
│
├── shared/                      # Shared utilities
│   └── types/                  # Shared TypeScript/Python types
│
├── infrastructure/              # IaC and deployment
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── docker-compose.prod.yml
│   │   └── docker-compose.test.yml
│   ├── kubernetes/             # K8s manifests (future)
│   └── terraform/              # Terraform (future)
│
├── scripts/                     # Development scripts
│   ├── setup-dev.sh
│   ├── run-tests.sh
│   └── migrate-db.sh
│
├── .github/
│   └── workflows/
│       ├── ci.yml              # Run tests
│       ├── deploy-staging.yml
│       └── deploy-prod.yml
│
├── docs/
│   ├── API.md                  # API documentation
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── CONTRIBUTING.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Phase 1: Foundation (Weeks 1-2)

### Week 1: Project Setup & Infrastructure

#### Day 1-2: Monorepo Setup
- [x] Create new monorepo structure
- [ ] Set up Docker Compose for local development
- [ ] Configure PostgreSQL container
- [ ] Configure Redis container
- [ ] Create development database schema
- [ ] Set up environment variables

#### Day 3-4: Backend Foundation
- [ ] Initialize FastAPI project (Poetry)
- [ ] Set up SQLAlchemy 2.0 models
- [ ] Create Alembic migrations
- [ ] Implement database connection pooling
- [ ] Add Redis client setup
- [ ] Create basic health check endpoint

#### Day 5-7: Frontend Foundation
- [ ] Initialize Next.js 14 project
- [ ] Set up TypeScript configuration
- [ ] Install and configure Tailwind CSS
- [ ] Install Shadcn/ui components
- [ ] Create basic layout components
- [ ] Set up API client (Axios/Fetch wrapper)

---

### Week 2: Authentication & Core Models

#### Day 8-10: Authentication
- [ ] Integrate Clerk.dev
- [ ] Create auth middleware (FastAPI)
- [ ] Implement JWT validation
- [ ] Add protected route HOC (React)
- [ ] Create login/signup pages
- [ ] Test auth flow end-to-end

#### Day 11-14: Core Data Models
- [ ] User model (synced from Clerk)
- [ ] Organization model
- [ ] Organization members model
- [ ] Repository model
- [ ] Scan model
- [ ] Create database seed script
- [ ] Write model unit tests

---

## Phase 2: Core Features (Weeks 3-6)

### Week 3: Organization Management

#### API Endpoints
```python
POST   /api/v1/organizations           # Create organization
GET    /api/v1/organizations           # List user's orgs
GET    /api/v1/organizations/{id}      # Get org details
PATCH  /api/v1/organizations/{id}      # Update org
DELETE /api/v1/organizations/{id}      # Delete org
```

#### Frontend Pages
- [ ] Organization list page
- [ ] Organization creation flow
- [ ] Organization settings page
- [ ] Team member invitation
- [ ] Role management (admin/member/viewer)

#### Tests
- [ ] API endpoint tests (pytest)
- [ ] React component tests (Vitest)
- [ ] E2E tests (Playwright)

---

### Week 4: Repository Management

#### API Endpoints
```python
POST   /api/v1/organizations/{id}/repositories  # Create repo
GET    /api/v1/organizations/{id}/repositories  # List repos
GET    /api/v1/repositories/{id}                # Get repo
PATCH  /api/v1/repositories/{id}                # Update repo
DELETE /api/v1/repositories/{id}                # Delete repo
```

#### Frontend Pages
- [ ] Repository list with search/filter
- [ ] Repository creation wizard
- [ ] Repository settings
- [ ] GitHub/GitLab integration UI

#### Backend Services
- [ ] Repository CRUD service
- [ ] Git integration service
- [ ] Access control checks

---

### Week 5: Scanning Engine Integration

#### Refactor Existing Scanner
```python
# OLD: Direct execution
result = builder.build(repo_path)

# NEW: Service-based with caching
from app.services.scan_service import ScanService

scan_service = ScanService(
    cache=redis_client,
    storage=s3_client
)

result = await scan_service.execute_scan(
    repository_id=repo.id,
    config=scan_config,
    user_id=current_user.id
)
```

#### Implement Celery Tasks
```python
# tasks/scan_tasks.py
from celery import Celery
from app.services.scan_service import ScanService

@celery.task(bind=True)
def run_scan(self, scan_id: str, repo_path: str, config: dict):
    """Run scan in background"""
    scan_service = ScanService()

    # Update progress callback
    def progress_callback(current, total, message):
        self.update_state(
            state='PROGRESS',
            meta={'current': current, 'total': total, 'message': message}
        )

    result = scan_service.execute_scan(
        scan_id=scan_id,
        repo_path=repo_path,
        config=config,
        progress_callback=progress_callback
    )

    return result
```

#### API Endpoints
```python
POST   /api/v1/repositories/{id}/scans     # Start scan
GET    /api/v1/scans/{id}                  # Get scan status
GET    /api/v1/scans/{id}/results          # Get results
POST   /api/v1/scans/{id}/cancel           # Cancel scan
WS     /ws/scans/{id}                      # WebSocket progress
```

#### Frontend Components
- [ ] Scan configuration form
- [ ] Scan progress indicator (with pinata!)
- [ ] Scan results visualization
- [ ] React Flow graph component
- [ ] Database schema view
- [ ] Export buttons (PDF, Excel, Confluence)

---

### Week 6: Caching & Performance

#### Implement Multi-Layer Caching

**Layer 1: File-Level Cache (Redis)**
```python
import hashlib
import redis

class FileCacheService:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def get_file_hash(self, file_path: str, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    async def get_cached_result(self, file_hash: str):
        cached = self.redis.get(f"file:{file_hash}")
        if cached:
            return json.loads(cached)
        return None

    async def cache_result(self, file_hash: str, result: dict):
        self.redis.setex(
            f"file:{file_hash}",
            86400,  # 24 hours
            json.dumps(result)
        )
```

**Layer 2: Scan-Level Cache (PostgreSQL + S3)**
```python
class ScanCacheService:
    async def get_incremental_scan_files(
        self,
        repository_id: str,
        last_scan_id: str
    ) -> List[str]:
        """Only return files that changed since last scan"""
        last_scan = await db.get_scan(last_scan_id)
        last_hashes = last_scan.file_hashes

        changed_files = []
        for file_path in discover_files(repo_path):
            current_hash = get_file_hash(file_path)
            if last_hashes.get(file_path) != current_hash:
                changed_files.append(file_path)

        return changed_files  # Could be 10-100x fewer files!
```

**Layer 3: API Response Cache (Redis)**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@router.get("/scans/{scan_id}")
@cache(expire=300)  # Cache for 5 minutes
async def get_scan(scan_id: str):
    return await db.get_scan(scan_id)
```

#### Database Query Optimization
```python
# Add indexes
CREATE INDEX idx_scans_repo_status ON scans(repository_id, status);
CREATE INDEX idx_scans_created ON scans(created_at DESC);
CREATE INDEX idx_org_members_user ON organization_members(user_id);

# Use select_related to avoid N+1 queries
scans = await db.execute(
    select(Scan)
    .options(selectinload(Scan.repository))  # Eager load
    .where(Scan.status == 'completed')
    .order_by(Scan.created_at.desc())
    .limit(20)
)
```

---

## Phase 3: Billing & Multi-Tenancy (Weeks 7-8)

### Week 7: Stripe Integration

#### Backend Implementation
```python
# services/billing_service.py
import stripe

class BillingService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create_checkout_session(
        self,
        organization_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ):
        org = await db.get_organization(organization_id)

        session = stripe.checkout.Session.create(
            customer_email=org.billing_email,
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'organization_id': organization_id}
        )

        return session

    async def handle_webhook(self, event: dict):
        """Handle Stripe webhooks"""
        if event['type'] == 'customer.subscription.created':
            await self.activate_subscription(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            await self.cancel_subscription(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            await self.handle_payment_failure(event['data']['object'])
```

#### API Endpoints
```python
POST /api/v1/billing/create-checkout      # Start subscription
POST /api/v1/billing/portal                # Customer portal
POST /api/v1/webhooks/stripe               # Stripe webhooks
GET  /api/v1/organizations/{id}/subscription  # Get subscription status
```

#### Frontend Pages
- [ ] Pricing page (public)
- [ ] Checkout flow
- [ ] Billing settings page
- [ ] Usage dashboard
- [ ] Invoice history

---

### Week 8: Usage Limits & Quota Enforcement

#### Middleware for Quota Checks
```python
# middleware/quota_middleware.py
from fastapi import HTTPException

async def check_scan_quota(
    organization_id: str,
    db: Session
):
    org = await db.get_organization(organization_id)
    subscription = await db.get_subscription(organization_id)

    # Check plan limits
    if subscription.plan == 'free':
        max_repos = 1
        max_scans_per_month = 10
    elif subscription.plan == 'team':
        max_repos = 10
        max_scans_per_month = 1000
    else:  # enterprise
        max_repos = -1  # unlimited
        max_scans_per_month = -1

    # Check repository limit
    repo_count = await db.count_repositories(organization_id)
    if max_repos > 0 and repo_count >= max_repos:
        raise HTTPException(
            status_code=403,
            detail=f"Repository limit reached. Upgrade to add more repositories."
        )

    # Check monthly scan limit
    current_month_scans = await db.count_scans_this_month(organization_id)
    if max_scans_per_month > 0 and current_month_scans >= max_scans_per_month:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly scan limit reached. Upgrade for more scans."
        )
```

#### Usage Tracking
```python
# Log all usage events
await db.create_usage_event(
    organization_id=org.id,
    event_type='scan_started',
    metadata={'repository_id': repo.id, 'files': 9161}
)
```

---

## Phase 4: Testing & Quality (Weeks 9-10)

### Testing Strategy

#### Backend Tests (pytest)

**Unit Tests** (70% coverage minimum)
```python
# tests/unit/services/test_scan_service.py
import pytest
from app.services.scan_service import ScanService

@pytest.fixture
def scan_service():
    return ScanService(cache=mock_redis, storage=mock_s3)

def test_file_hash_calculation(scan_service):
    content = b"test content"
    hash1 = scan_service.get_file_hash(content)
    hash2 = scan_service.get_file_hash(content)
    assert hash1 == hash2  # Deterministic

def test_incremental_scan_only_changed_files(scan_service):
    # Setup: previous scan with file hashes
    # Act: run incremental scan
    # Assert: only changed files scanned
    pass

@pytest.mark.asyncio
async def test_scan_with_cache_hit(scan_service):
    # Given: file result in cache
    # When: scan same file
    # Then: cache hit, no re-scanning
    pass
```

**Integration Tests** (API endpoints)
```python
# tests/integration/test_scans_api.py
from fastapi.testclient import TestClient

def test_create_scan_endpoint(client: TestClient, test_user):
    response = client.post(
        f"/api/v1/repositories/{repo_id}/scans",
        headers={"Authorization": f"Bearer {test_user.token}"},
        json={"config": {"file_extensions": [".cs", ".ts"]}}
    )
    assert response.status_code == 202
    assert "scan_id" in response.json()

def test_scan_quota_enforcement(client: TestClient, free_tier_user):
    # Create 10 scans (free tier limit)
    for _ in range(10):
        client.post(f"/api/v1/repositories/{repo_id}/scans", ...)

    # 11th scan should fail
    response = client.post(f"/api/v1/repositories/{repo_id}/scans", ...)
    assert response.status_code == 403
    assert "limit reached" in response.json()["detail"]
```

**E2E Tests** (Playwright)
```python
# tests/e2e/test_scan_workflow.py
async def test_complete_scan_flow(page):
    # Login
    await page.goto("http://localhost:3000/login")
    await page.fill('input[name="email"]', "test@example.com")
    await page.click('button[type="submit"]')

    # Create repository
    await page.goto("/repositories/new")
    await page.fill('input[name="name"]', "Test Repo")
    await page.click('button:has-text("Create")')

    # Start scan
    await page.click('button:has-text("Start Scan")')

    # Wait for completion
    await page.wait_for_selector('text=Scan complete', timeout=60000)

    # Verify results displayed
    assert await page.is_visible('text=Files Scanned')
```

#### Frontend Tests (Vitest + React Testing Library)

```typescript
// components/__tests__/ScanProgress.test.tsx
import { render, screen } from '@testing-library/react';
import { ScanProgress } from '../ScanProgress';

test('displays progress bar with pinata', () => {
  render(<ScanProgress current={50} total={100} />);

  expect(screen.getByRole('progressbar')).toBeInTheDocument();
  expect(screen.getByText('🪅')).toBeInTheDocument();
  expect(screen.getByText('50%')).toBeInTheDocument();
});

test('pinata moves with progress', async () => {
  const { rerender } = render(<ScanProgress current={25} total={100} />);

  const pinata1 = screen.getByTestId('pinata');
  const position1 = pinata1.style.left;

  rerender(<ScanProgress current={75} total={100} />);

  const pinata2 = screen.getByTestId('pinata');
  const position2 = pinata2.style.left;

  expect(position2).not.toBe(position1);  // Moved
});
```

#### Load Testing (Locust)

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class PinataCodeUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": "load-test@example.com",
            "password": "test123"
        })
        self.token = response.json()["access_token"]

    @task(3)
    def list_scans(self):
        self.client.get(
            "/api/v1/scans",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def start_scan(self):
        self.client.post(
            f"/api/v1/repositories/{self.repo_id}/scans",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"config": {"file_extensions": [".cs"]}}
        )

# Run: locust -f tests/load/locustfile.py --users 100 --spawn-rate 10
```

---

## Phase 5: Deployment & Monitoring (Weeks 11-12)

### Docker Configuration

**docker-compose.yml** (Development)
```yaml
version: '3.9'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./scanner:/scanner
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/pinata_dev
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
      - ./scanner:/scanner
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/pinata_dev
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    command: celery -A app.tasks worker --loglevel=info

  db:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=pinata_dev
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### CI/CD Pipeline

**.github/workflows/ci.yml**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install poetry
          poetry install

      - name: Run tests
        run: |
          cd backend
          poetry run pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm run test

      - name: Run linter
        run: |
          cd frontend
          npm run lint

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Start services
        run: docker-compose -f docker-compose.test.yml up -d

      - name: Run E2E tests
        run: |
          npm run test:e2e

      - name: Stop services
        run: docker-compose -f docker-compose.test.yml down
```

### Monitoring Setup

**Sentry (Error Tracking)**
```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    integrations=[FastApiIntegration()],
    environment=settings.ENVIRONMENT
)
```

```typescript
// frontend/app/layout.tsx
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
});
```

**PostHog (Product Analytics)**
```typescript
// frontend/lib/analytics.ts
import posthog from 'posthog-js';

posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  api_host: 'https://app.posthog.com',
});

export const analytics = {
  track: (event: string, properties?: Record<string, any>) => {
    posthog.capture(event, properties);
  },
  identify: (userId: string, traits?: Record<string, any>) => {
    posthog.identify(userId, traits);
  },
};
```

---

## Success Metrics

### Phase 1 (Weeks 1-2): Foundation
- [ ] Docker Compose starts all services
- [ ] Database migrations run successfully
- [ ] Health check endpoints return 200
- [ ] Frontend loads at localhost:3000
- [ ] Backend API docs at localhost:8000/docs

### Phase 2 (Weeks 3-6): Core Features
- [ ] User can create organization
- [ ] User can add repository
- [ ] User can trigger scan
- [ ] Scan completes successfully
- [ ] Results display in UI
- [ ] 80% test coverage

### Phase 3 (Weeks 7-8): Billing
- [ ] Stripe checkout works
- [ ] Webhooks process correctly
- [ ] Quota enforcement works
- [ ] Subscription status shows in UI

### Phase 4 (Weeks 9-10): Quality
- [ ] All tests passing
- [ ] Load tests handle 100 concurrent users
- [ ] API response times <200ms (p95)
- [ ] No critical security vulnerabilities

### Phase 5 (Weeks 11-12): Deployment
- [ ] CI/CD pipeline green
- [ ] Staging environment live
- [ ] Production environment live
- [ ] Monitoring dashboards configured
- [ ] Incident response plan documented

---

## Development Workflow

### Daily Workflow
```bash
# Start all services
docker-compose up -d

# Run backend tests
cd backend && poetry run pytest

# Run frontend tests
cd frontend && npm test

# Check logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

### Database Migrations
```bash
# Create migration
cd backend
poetry run alembic revision --autogenerate -m "Add users table"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### Git Workflow
```bash
# Feature branch
git checkout -b feature/scan-caching

# Commit with conventional commits
git commit -m "feat(scan): add incremental scanning support"

# Push and create PR
git push origin feature/scan-caching
```

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | 2 weeks | Foundation + Auth |
| **Phase 2** | 4 weeks | Core Features |
| **Phase 3** | 2 weeks | Billing + Multi-tenancy |
| **Phase 4** | 2 weeks | Testing + Quality |
| **Phase 5** | 2 weeks | Deployment + Monitoring |
| **Total** | **12 weeks** | **Production-ready SaaS** |

---

## Next Immediate Steps

1. **Today**: Create monorepo structure
2. **This Week**: Docker Compose + Database setup
3. **Next Week**: FastAPI backend + React frontend skeletons
4. **Week 3**: Start building features

Ready to begin? Let's start with the monorepo structure and Docker setup!

---

**Document Version**: 1.0
**Last Updated**: October 31, 2025
**Author**: Claude (AI Assistant)
**Status**: Implementation Roadmap - APPROVED FOR EXECUTION
