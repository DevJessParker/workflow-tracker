# Scalable SaaS Architecture for Pinata Code

## Executive Summary

This document outlines the recommended architecture for transforming Pinata Code from a standalone tool into a scalable, multi-tenant SaaS platform capable of supporting thousands of customers with enterprise features.

**Current State**: Single-user desktop application (Streamlit GUI + CLI)

**Target State**: Multi-tenant web application with:
- User authentication & authorization
- Subscription management & billing
- Customer dashboards
- Team collaboration
- Enterprise integrations
- API access
- Analytics & monitoring

**Recommended Stack**: Modern, proven technologies optimized for fast development and scalability.

---

## 🏗️ Recommended Technology Stack

### Frontend Framework: **React + Next.js**

**Why Not Streamlit for Production SaaS:**
- ❌ Not designed for multi-user applications
- ❌ Limited state management for complex interactions
- ❌ Poor performance with large datasets (31K+ nodes)
- ❌ Difficult to implement custom auth/billing flows
- ❌ No SSR (server-side rendering) for SEO
- ❌ Limited control over UI/UX

**Why React + Next.js:**
- ✅ Industry standard for SaaS applications
- ✅ Excellent performance with code splitting
- ✅ SSR for SEO and initial page load
- ✅ Rich ecosystem (components, libraries)
- ✅ Easy to hire developers
- ✅ Can embed Streamlit for specific visualizations if needed

**Alternative**: Vue.js + Nuxt.js (similar benefits, smaller ecosystem)

### Backend Framework: **FastAPI (Python)** or **Node.js + Express**

**Option 1: FastAPI (Python) - RECOMMENDED**

**Why FastAPI:**
- ✅ Keep existing Python codebase (scanning logic)
- ✅ Excellent performance (async/await)
- ✅ Auto-generated API documentation (Swagger)
- ✅ Built-in validation (Pydantic)
- ✅ Easy to build REST and WebSocket APIs
- ✅ Modern, growing ecosystem

**When to use**:
- You want to minimize rewrite (keep Python scanning engine)
- Team is comfortable with Python
- Performance requirements are moderate (<10K requests/sec)

**Option 2: Node.js + Express (TypeScript)**

**Why Node.js:**
- ✅ Same language as frontend (TypeScript)
- ✅ Excellent for real-time features (WebSockets)
- ✅ Rich NPM ecosystem
- ✅ Easy horizontal scaling

**When to use**:
- Team prefers JavaScript/TypeScript everywhere
- Heavy real-time features (live scan progress)
- Want single language stack

**My Recommendation**: **FastAPI** - Keep your Python investment, excellent for APIs, great documentation.

---

## 🗂️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT TIER                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Web App    │  │   CLI Tool   │  │  CI/CD       │             │
│  │  (Next.js)   │  │   (Python)   │  │  Integrations│             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                  │                     │
└─────────┼─────────────────┼──────────────────┼─────────────────────┘
          │                 │                  │
          │                 └──────────┬───────┘
          │                            │
┌─────────┼────────────────────────────┼─────────────────────────────┐
│         │        API GATEWAY TIER    │                             │
├─────────┼────────────────────────────┼─────────────────────────────┤
│         │                            │                             │
│    ┌────▼────────────────────────────▼──────┐                      │
│    │      API Gateway (Kong/Nginx)          │                      │
│    │  - Rate limiting                       │                      │
│    │  - Authentication                      │                      │
│    │  - Request routing                     │                      │
│    └────┬──────────────────────┬────────────┘                      │
│         │                      │                                   │
└─────────┼──────────────────────┼───────────────────────────────────┘
          │                      │
┌─────────┼──────────────────────┼───────────────────────────────────┐
│         │   APPLICATION TIER   │                                   │
├─────────┼──────────────────────┼───────────────────────────────────┤
│         │                      │                                   │
│    ┌────▼────────┐    ┌────────▼──────┐    ┌──────────────┐       │
│    │   FastAPI   │    │  Scan Worker  │    │   Scheduler  │       │
│    │  REST API   │    │   (Celery)    │    │   (Celery    │       │
│    │             │    │               │    │    Beat)     │       │
│    └─────┬───────┘    └───────┬───────┘    └──────┬───────┘       │
│          │                    │                   │               │
│          │    ┌───────────────┴───────┬───────────┘               │
│          │    │                       │                           │
└──────────┼────┼───────────────────────┼───────────────────────────┘
           │    │                       │
┌──────────┼────┼───────────────────────┼───────────────────────────┐
│          │    │    DATA TIER          │                           │
├──────────┼────┼───────────────────────┼───────────────────────────┤
│          │    │                       │                           │
│  ┌───────▼────▼───┐   ┌───────────────▼──┐   ┌─────────────┐     │
│  │   PostgreSQL   │   │     Redis        │   │  S3/Minio   │     │
│  │  - Users       │   │  - Sessions      │   │  - Scans    │     │
│  │  - Orgs        │   │  - Cache         │   │  - Exports  │     │
│  │  - Subs        │   │  - Job queue     │   │  - Uploads  │     │
│  └────────────────┘   └──────────────────┘   └─────────────┘     │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                               │
├───────────────────────────────────────────────────────────────────┤
│  • Stripe (Payments)        • SendGrid (Email)                    │
│  • Auth0/Clerk (Auth)       • Datadog/Sentry (Monitoring)         │
│  • Cloudflare (CDN)         • GitHub/GitLab (OAuth)               │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Authentication & Authorization

### Recommended Solution: **Clerk.dev** (Primary) or **Auth0** (Enterprise)

#### Why Clerk
- ✅ Drop-in React components (sign-in, sign-up, user profile)
- ✅ Built-in user management UI
- ✅ Organization/team support out of the box
- ✅ Free tier: 5K MAU (monthly active users)
- ✅ SAML/SSO available (enterprise)
- ✅ Excellent DX (developer experience)

**Pricing**:
- Free: 5K MAU
- Pro: $25/month + $0.02/MAU
- Enterprise: Custom (SSO, advanced security)

#### Why Auth0
- ✅ More mature, enterprise-proven
- ✅ Better compliance (SOC2, HIPAA)
- ✅ More customizable
- ❌ More expensive ($240/month min)
- ❌ Steeper learning curve

**My Recommendation**: **Clerk** for Phase 1-2, migrate to Auth0 if enterprise demands it.

### Alternative: Roll Your Own (NOT RECOMMENDED)

**Why NOT to build custom auth**:
- ⏱️ 2-3 months of dev time
- 🔒 Security risks (password hashing, session management, MFA)
- 🛠️ Ongoing maintenance (password reset, email verification, etc.)
- 💰 Hidden costs (email service, SMS for MFA)

**Only build custom if**:
- Extreme cost sensitivity (>100K users)
- Unique security requirements (government, defense)

---

## 💳 Payment & Subscription Management

### Recommended Solution: **Stripe Billing** + **Stripe Checkout**

#### Why Stripe
- ✅ Industry standard (trusted by users)
- ✅ Handles complex scenarios (trials, upgrades, proration)
- ✅ Tax calculation (Stripe Tax)
- ✅ Invoicing & receipts
- ✅ PCI compliance built-in
- ✅ Webhooks for subscription events
- ✅ Customer portal (self-service)

**Pricing**: 2.9% + $0.30 per transaction

#### Architecture with Stripe

```python
# Backend: FastAPI
from stripe import Stripe
from fastapi import APIRouter

router = APIRouter()

@router.post("/create-checkout-session")
async def create_checkout(plan: str, user_id: str):
    """Create Stripe checkout session for subscription"""
    session = stripe.checkout.Session.create(
        customer_email=user.email,
        line_items=[{
            'price': PRICE_IDS[plan],  # Team: price_xxx, Enterprise: price_yyy
            'quantity': 1,
        }],
        mode='subscription',
        success_url='https://app.pinatacode.com/success',
        cancel_url='https://app.pinatacode.com/pricing',
        metadata={
            'user_id': user_id,
            'plan': plan,
        }
    )
    return {"url": session.url}

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe events (subscription created, cancelled, etc.)"""
    event = stripe.Webhook.construct_event(
        payload=await request.body(),
        sig_header=request.headers['stripe-signature'],
        secret=STRIPE_WEBHOOK_SECRET
    )

    if event.type == 'customer.subscription.created':
        # Activate user's subscription in database
        await activate_subscription(event.data.object)
    elif event.type == 'customer.subscription.deleted':
        # Downgrade user to free tier
        await deactivate_subscription(event.data.object)

    return {"status": "success"}
```

**Frontend: Next.js**

```typescript
// app/pricing/page.tsx
import { loadStripe } from '@stripe/stripe-js';

export default function Pricing() {
  const handleSubscribe = async (plan: string) => {
    const response = await fetch('/api/create-checkout-session', {
      method: 'POST',
      body: JSON.stringify({ plan }),
    });
    const { url } = await response.json();
    window.location.href = url; // Redirect to Stripe checkout
  };

  return (
    <div>
      <button onClick={() => handleSubscribe('team')}>
        Subscribe to Team ($49/month)
      </button>
    </div>
  );
}
```

### Alternative: Paddle (Merchant of Record)

**Pros**:
- Handles VAT/tax globally
- Simpler compliance
- Good for international sales

**Cons**:
- Higher fees (5% + payment processing)
- Less flexible than Stripe

**Use Paddle if**: Selling heavily in EU/international markets

---

## 📊 Database Schema

### Primary Database: **PostgreSQL**

**Why Postgres**:
- ✅ Robust, proven at scale
- ✅ JSONB for flexible schemas (store scan results)
- ✅ Full-text search
- ✅ Row-level security (RLS) for multi-tenancy
- ✅ Excellent Python support (SQLAlchemy, Psycopg)

### Schema Design

```sql
-- Users table (synced from Clerk/Auth0)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    auth_provider_id VARCHAR(255) UNIQUE NOT NULL, -- Clerk user ID
    name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Organizations (teams/companies)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL, -- acme-corp
    plan VARCHAR(50) DEFAULT 'free', -- free, team, enterprise
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    subscription_status VARCHAR(50), -- active, past_due, canceled
    max_repositories INT DEFAULT 1,
    max_seats INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Organization members
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- admin, member, viewer
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- Repositories (codebases)
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    remote_url TEXT, -- GitHub, GitLab URL
    default_branch VARCHAR(100) DEFAULT 'main',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scans (execution history)
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    triggered_by UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    files_scanned INT DEFAULT 0,
    nodes_found INT DEFAULT 0,
    edges_found INT DEFAULT 0,
    scan_time_seconds FLOAT,
    error_message TEXT,
    result_data JSONB, -- Full scan results (graph nodes/edges)
    result_s3_key VARCHAR(500), -- S3 path for large results
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scan configurations (saved settings)
CREATE TABLE scan_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) DEFAULT 'Default',
    file_extensions TEXT[], -- ['.cs', '.ts', '.js']
    exclude_dirs TEXT[], -- ['node_modules', 'bin']
    detect_database BOOLEAN DEFAULT true,
    detect_api BOOLEAN DEFAULT true,
    detect_file_io BOOLEAN DEFAULT true,
    detect_message_queues BOOLEAN DEFAULT true,
    detect_transforms BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Integrations (Confluence, Slack, etc.)
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- confluence, slack, jira
    config JSONB NOT NULL, -- Store API keys, URLs, etc. (encrypted)
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API keys (for programmatic access)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- "CI/CD Pipeline"
    key_hash VARCHAR(255) UNIQUE NOT NULL, -- Hashed API key
    key_prefix VARCHAR(20), -- First few chars for display
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

-- Usage tracking (for analytics and billing)
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- scan_started, scan_completed, export_generated
    metadata JSONB, -- Additional event data
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_scans_repository ON scans(repository_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_org_members_user ON organization_members(user_id);
CREATE INDEX idx_usage_events_org ON usage_events(organization_id);
CREATE INDEX idx_usage_events_created ON usage_events(created_at);
```

---

## ⚡ Caching & Job Queue

### Redis (Multi-purpose)

**Use cases**:
1. **Session storage** (user sessions, OAuth tokens)
2. **Caching** (API responses, scan results)
3. **Rate limiting** (API throttling)
4. **Job queue** (Celery broker)
5. **Real-time updates** (Pub/Sub for scan progress)

```python
# Example: Cache scan results
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_scan_results(scan_id: str):
    # Check cache first
    cached = redis_client.get(f"scan:{scan_id}")
    if cached:
        return json.loads(cached)

    # Fetch from database
    scan = await db.query("SELECT * FROM scans WHERE id = ?", scan_id)

    # Cache for 1 hour
    redis_client.setex(f"scan:{scan_id}", 3600, json.dumps(scan))

    return scan
```

### Celery (Background Jobs)

**Use cases**:
1. Run scans asynchronously (long-running tasks)
2. Scheduled scans (nightly/weekly)
3. Export generation (PDF, Excel)
4. Email notifications
5. Confluence publishing

```python
# tasks.py
from celery import Celery

celery_app = Celery('pinata', broker='redis://localhost:6379/0')

@celery_app.task
def run_scan(repository_id: str, config: dict):
    """Run scan in background"""
    # Update scan status to 'running'
    await update_scan_status(scan_id, 'running')

    try:
        # Run scanning logic
        builder = WorkflowGraphBuilder(config)
        result = builder.build(repo_path)

        # Store results
        await save_scan_results(scan_id, result)

        # Update status to 'completed'
        await update_scan_status(scan_id, 'completed')

        # Send notification
        await send_email_notification(user, "Scan complete!")

    except Exception as e:
        await update_scan_status(scan_id, 'failed', error=str(e))
        await send_error_notification(user, str(e))

# API endpoint triggers task
@router.post("/repositories/{repo_id}/scan")
async def trigger_scan(repo_id: str):
    scan = await create_scan_record(repo_id)
    run_scan.delay(repo_id, config)  # Async execution
    return {"scan_id": scan.id, "status": "pending"}
```

---

## 📦 File Storage (S3 or MinIO)

### Why Not Store Everything in Database

**Large scan results** (31K+ nodes) should go to object storage:
- ✅ Lower cost ($0.023/GB vs. $0.10-0.50/GB for DB)
- ✅ Better performance (database optimized for queries, not large blobs)
- ✅ Easier backups
- ✅ CDN integration (serve exports directly to users)

### Architecture

```python
# Store large results in S3, metadata in Postgres
import boto3

s3_client = boto3.client('s3')

def save_scan_results(scan_id: str, result: ScanResult):
    # Serialize result
    result_json = json.dumps(result.to_dict())

    # Upload to S3
    s3_key = f"scans/{scan_id}/result.json"
    s3_client.put_object(
        Bucket='pinata-scan-results',
        Key=s3_key,
        Body=result_json,
        ContentType='application/json'
    )

    # Store metadata in Postgres
    await db.execute("""
        UPDATE scans
        SET result_s3_key = ?, nodes_found = ?, edges_found = ?, status = 'completed'
        WHERE id = ?
    """, s3_key, len(result.graph.nodes), len(result.graph.edges), scan_id)

def get_scan_results(scan_id: str):
    # Get S3 key from database
    scan = await db.fetchone("SELECT result_s3_key FROM scans WHERE id = ?", scan_id)

    # Download from S3
    response = s3_client.get_object(Bucket='pinata-scan-results', Key=scan['result_s3_key'])
    result_json = response['Body'].read()

    return json.loads(result_json)
```

**Alternatives**:
- **MinIO** (self-hosted S3-compatible) - Good for on-premise deployments
- **Cloudflare R2** - Cheaper egress, good for serving files to users

---

## 🖥️ Frontend Architecture (Next.js)

### Folder Structure

```
app/
├── (auth)/                     # Auth-protected routes
│   ├── dashboard/
│   │   └── page.tsx           # Main dashboard
│   ├── repositories/
│   │   ├── page.tsx           # List repositories
│   │   └── [id]/
│   │       ├── page.tsx       # Repository detail
│   │       └── scans/
│   │           └── [scanId]/
│   │               └── page.tsx  # Scan results view
│   ├── settings/
│   │   ├── profile/page.tsx
│   │   ├── organization/page.tsx
│   │   └── billing/page.tsx
│   └── layout.tsx             # Protected layout (check auth)
├── (marketing)/               # Public routes
│   ├── page.tsx               # Homepage
│   ├── pricing/page.tsx
│   ├── docs/page.tsx
│   └── layout.tsx             # Marketing layout
├── api/
│   ├── scans/
│   │   └── route.ts           # API route handlers
│   └── webhooks/
│       └── stripe/route.ts
└── layout.tsx                 # Root layout

components/
├── ui/                        # Shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   └── ...
├── scan-results/
│   ├── workflow-graph.tsx     # D3.js or React Flow visualization
│   ├── database-schema.tsx
│   └── metrics-cards.tsx
└── dashboard/
    ├── sidebar.tsx
    └── navbar.tsx

lib/
├── api-client.ts              # Axios/Fetch wrapper for API calls
├── auth.ts                    # Clerk/Auth0 integration
└── utils.ts
```

### Key Frontend Technologies

| Tool | Purpose | Why |
|------|---------|-----|
| **Next.js 14** | React framework | SSR, routing, API routes |
| **TypeScript** | Type safety | Catch bugs early, better DX |
| **Tailwind CSS** | Styling | Fast, consistent, responsive |
| **Shadcn/ui** | Component library | Beautiful, accessible, customizable |
| **React Query** | Data fetching | Caching, optimistic updates |
| **React Flow** | Graph visualization | Better than D3 for complex workflows |
| **Zustand** | State management | Simpler than Redux |

### Example: Scan Results View

```typescript
// app/(auth)/repositories/[id]/scans/[scanId]/page.tsx
import { useQuery } from '@tanstack/react-query';
import { WorkflowGraph } from '@/components/scan-results/workflow-graph';

export default function ScanDetailPage({ params }: { params: { scanId: string } }) {
  const { data: scan, isLoading } = useQuery({
    queryKey: ['scan', params.scanId],
    queryFn: () => fetch(`/api/scans/${params.scanId}`).then(res => res.json()),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Scan Results</h1>

      <div className="grid grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader>Files Scanned</CardHeader>
          <CardContent className="text-3xl font-bold">
            {scan.files_scanned.toLocaleString()}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>Workflow Nodes</CardHeader>
          <CardContent className="text-3xl font-bold">
            {scan.nodes_found.toLocaleString()}
          </CardContent>
        </Card>
        {/* More metrics... */}
      </div>

      <Tabs defaultValue="graph">
        <TabsList>
          <TabsTrigger value="graph">Workflow Graph</TabsTrigger>
          <TabsTrigger value="database">Database Schema</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="graph">
          <WorkflowGraph data={scan.result_data} />
        </TabsContent>

        {/* More tabs... */}
      </Tabs>
    </div>
  );
}
```

---

## 🔌 API Design (FastAPI)

### RESTful Endpoints

```
Authentication (via Clerk/Auth0)
├── POST   /auth/callback          # OAuth callback
└── POST   /auth/logout            # Logout

Organizations
├── GET    /organizations          # List user's orgs
├── POST   /organizations          # Create new org
├── GET    /organizations/:id      # Get org details
├── PATCH  /organizations/:id      # Update org
└── DELETE /organizations/:id      # Delete org

Organization Members
├── GET    /organizations/:id/members       # List members
├── POST   /organizations/:id/members       # Invite member
└── DELETE /organizations/:id/members/:uid  # Remove member

Repositories
├── GET    /organizations/:id/repositories  # List repos
├── POST   /organizations/:id/repositories  # Create repo
├── GET    /repositories/:id                # Get repo
├── PATCH  /repositories/:id                # Update repo
└── DELETE /repositories/:id                # Delete repo

Scans
├── GET    /repositories/:id/scans          # List scans
├── POST   /repositories/:id/scans          # Start scan
├── GET    /scans/:id                       # Get scan details
├── GET    /scans/:id/results               # Get full results
├── POST   /scans/:id/cancel                # Cancel running scan
└── DELETE /scans/:id                       # Delete scan

Exports
├── POST   /scans/:id/exports/pdf           # Generate PDF
├── POST   /scans/:id/exports/excel         # Generate Excel
└── POST   /scans/:id/exports/confluence    # Publish to Confluence

Integrations
├── GET    /organizations/:id/integrations  # List integrations
├── POST   /organizations/:id/integrations  # Add integration
├── PATCH  /integrations/:id                # Update integration
└── DELETE /integrations/:id                # Remove integration

Billing (Stripe)
├── POST   /billing/create-checkout         # Start subscription
├── POST   /billing/portal                  # Customer portal
└── POST   /webhooks/stripe                 # Stripe webhooks

API Keys
├── GET    /organizations/:id/api-keys      # List keys
├── POST   /organizations/:id/api-keys      # Create key
└── DELETE /api-keys/:id                    # Revoke key

Analytics
├── GET    /organizations/:id/usage         # Usage stats
└── GET    /scans/:id/metrics               # Scan metrics
```

### Example Implementation

```python
# api/routers/scans.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models import Scan, ScanCreate
from ..auth import get_current_user
from ..tasks import run_scan

router = APIRouter()

@router.get("/repositories/{repo_id}/scans", response_model=List[Scan])
async def list_scans(
    repo_id: str,
    user=Depends(get_current_user)
):
    """List all scans for a repository"""
    # Check user has access to this repo
    await check_repo_access(user, repo_id)

    scans = await db.fetch_all(
        "SELECT * FROM scans WHERE repository_id = ? ORDER BY created_at DESC",
        repo_id
    )
    return scans

@router.post("/repositories/{repo_id}/scans", status_code=202)
async def create_scan(
    repo_id: str,
    config: ScanCreate,
    user=Depends(get_current_user)
):
    """Start a new scan"""
    # Check user has access and quota
    await check_repo_access(user, repo_id)
    await check_scan_quota(user.organization_id)

    # Create scan record
    scan = await db.execute("""
        INSERT INTO scans (repository_id, triggered_by, status)
        VALUES (?, ?, 'pending')
        RETURNING *
    """, repo_id, user.id)

    # Queue background job
    run_scan.delay(scan['id'], config.dict())

    return {
        "scan_id": scan['id'],
        "status": "pending",
        "message": "Scan queued successfully"
    }

@router.get("/scans/{scan_id}/results")
async def get_scan_results(
    scan_id: str,
    user=Depends(get_current_user)
):
    """Get full scan results"""
    scan = await db.fetch_one("SELECT * FROM scans WHERE id = ?", scan_id)

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Check access
    await check_scan_access(user, scan_id)

    # Fetch from S3
    results = await get_scan_from_s3(scan['result_s3_key'])

    return {
        "scan": scan,
        "results": results
    }
```

---

## 🚀 Deployment Architecture

### Recommended: **Vercel (Frontend) + Railway/Render (Backend)**

#### Option 1: Vercel + Railway (RECOMMENDED)

```
Frontend (Next.js):
└── Vercel
    ├── Auto-deploys from GitHub
    ├── Edge CDN (global)
    ├── Serverless functions for API routes
    └── $20/month (Pro plan)

Backend (FastAPI):
└── Railway.app
    ├── Postgres database (included)
    ├── Redis (included)
    ├── Auto-deploys from GitHub
    ├── Horizontal scaling
    └── $5-20/month (Hobby → Starter)

Workers (Celery):
└── Railway.app (separate service)
    └── Same infrastructure, different container

Storage:
└── AWS S3 or Cloudflare R2
    └── $5-50/month depending on usage
```

**Total Cost**: $30-90/month for <1,000 users

#### Option 2: AWS (Enterprise-ready)

```
Frontend:
└── AWS Amplify or CloudFront + S3
    ├── Global CDN
    └── $50-200/month

Backend:
└── AWS ECS (Fargate) or Lambda
    ├── Auto-scaling
    ├── Load balancer (ALB)
    └── $100-500/month

Database:
└── AWS RDS (Postgres)
    ├── Multi-AZ for HA
    └── $50-300/month

Cache/Queue:
└── AWS ElastiCache (Redis)
    └── $30-150/month

Storage:
└── AWS S3
    └── $10-100/month
```

**Total Cost**: $240-1,250/month for 1K-10K users

**Use AWS when**:
- Enterprise customers require it
- Need compliance (HIPAA, SOC2)
- Self-hosted/on-premise option needed

#### Option 3: Kubernetes (Advanced)

**Use K8s when**:
- >10K concurrent users
- Complex microservices architecture
- Multi-region deployment
- You have DevOps expertise

**Not recommended for early stage** - overkill and expensive.

---

## 📡 Real-time Updates (WebSockets)

### For Live Scan Progress

**Technology**: FastAPI WebSockets + Redis Pub/Sub

```python
# Backend: WebSocket endpoint
from fastapi import WebSocket

@app.websocket("/ws/scans/{scan_id}")
async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    await websocket.accept()

    # Subscribe to Redis channel for this scan
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"scan:{scan_id}:progress")

    try:
        async for message in pubsub.listen():
            if message['type'] == 'message':
                # Forward progress update to client
                await websocket.send_json(json.loads(message['data']))
    except WebSocketDisconnect:
        await pubsub.unsubscribe(f"scan:{scan_id}:progress")

# In scanning code: Publish progress
def update_progress(current, total, message):
    redis_client.publish(
        f"scan:{scan_id}:progress",
        json.dumps({
            'current': current,
            'total': total,
            'message': message,
            'progress': current / total
        })
    )
```

**Frontend: React hook**

```typescript
// hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

export function useScanProgress(scanId: string) {
  const [progress, setProgress] = useState({ current: 0, total: 0, message: '' });

  useEffect(() => {
    const ws = new WebSocket(`wss://api.pinatacode.com/ws/scans/${scanId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
    };

    return () => ws.close();
  }, [scanId]);

  return progress;
}

// In component
function ScanProgress({ scanId }) {
  const { current, total, message, progress } = useScanProgress(scanId);

  return (
    <div>
      <ProgressBar value={progress * 100} />
      <p>{message}</p>
      <p>{current} / {total} files</p>
    </div>
  );
}
```

---

## 🛡️ Security Best Practices

### 1. API Security

```python
# Rate limiting (per user, per endpoint)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/scans")
@limiter.limit("60/minute")  # Max 60 requests per minute
async def list_scans():
    ...

# API key authentication
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    key_hash = hash_api_key(api_key)

    key_record = await db.fetch_one(
        "SELECT * FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL",
        key_hash
    )

    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Update last used
    await db.execute("UPDATE api_keys SET last_used_at = NOW() WHERE id = ?", key_record['id'])

    return key_record

# Use in endpoint
@app.get("/api/scans", dependencies=[Depends(verify_api_key)])
async def list_scans_api():
    ...
```

### 2. Data Encryption

```python
# Encrypt sensitive integration configs (Confluence API keys, etc.)
from cryptography.fernet import Fernet

# Store encryption key in environment variable
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_integration_config(config: dict) -> str:
    json_data = json.dumps(config)
    encrypted = cipher.encrypt(json_data.encode())
    return encrypted.decode()

def decrypt_integration_config(encrypted: str) -> dict:
    decrypted = cipher.decrypt(encrypted.encode())
    return json.loads(decrypted.decode())

# When saving integration
await db.execute("""
    INSERT INTO integrations (organization_id, type, config)
    VALUES (?, ?, ?)
""", org_id, 'confluence', encrypt_integration_config({
    'url': 'https://company.atlassian.net',
    'api_key': 'secret_key_here',
    'space_key': 'DOCS'
}))
```

### 3. Input Validation

```python
from pydantic import BaseModel, validator

class ScanConfigCreate(BaseModel):
    file_extensions: list[str]
    exclude_dirs: list[str]

    @validator('file_extensions')
    def validate_extensions(cls, v):
        # Only allow certain extensions
        allowed = {'.cs', '.ts', '.js', '.java', '.py', '.go'}
        for ext in v:
            if ext not in allowed:
                raise ValueError(f"Extension {ext} not supported")
        return v

    @validator('exclude_dirs')
    def validate_excludes(cls, v):
        # Prevent path traversal
        for dir in v:
            if '..' in dir or dir.startswith('/'):
                raise ValueError("Invalid exclude path")
        return v
```

---

## 📊 Monitoring & Observability

### Recommended: **Sentry (Errors) + Datadog/New Relic (APM)**

```python
# Initialize Sentry
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project",
    traces_sample_rate=0.1,  # Sample 10% of transactions
    integrations=[FastApiIntegration()],
    environment=os.getenv('ENVIRONMENT', 'production')
)

# Automatic error tracking
@app.get("/scans/{scan_id}")
async def get_scan(scan_id: str):
    # Any unhandled exception automatically sent to Sentry
    scan = await db.fetch_one("SELECT * FROM scans WHERE id = ?", scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found")  # Logged in Sentry
    return scan

# Custom events
sentry_sdk.capture_message(f"Scan completed: {scan_id}")
```

### Metrics to Track

**Business Metrics**:
- Monthly Recurring Revenue (MRR)
- Customer Acquisition Cost (CAC)
- Lifetime Value (LTV)
- Churn rate
- Daily/Weekly/Monthly Active Users

**Technical Metrics**:
- API response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Database query performance
- Scan completion time
- Queue length (Celery)

**Product Metrics**:
- Scans per user per month
- Average nodes per scan
- Feature usage (Confluence publish, exports)
- Time to first scan (onboarding)

---

## 🔄 Migration Path from Streamlit

### Phase 1: Hybrid Approach (Quick Win)

**Keep Streamlit for visualizations**, wrap it in Next.js app:

```typescript
// app/scans/[id]/page.tsx
export default function ScanDetailPage({ params }) {
  return (
    <div>
      <h1>Scan Results</h1>
      {/* Embed Streamlit in iframe */}
      <iframe
        src={`http://streamlit-service:8501?scan_id=${params.id}`}
        width="100%"
        height="800px"
      />
    </div>
  );
}
```

**Pros**:
- ✅ Fast to implement (reuse existing code)
- ✅ Focus on building auth/billing first

**Cons**:
- ❌ Poor UX (iframe limitations)
- ❌ Not scalable long-term

### Phase 2: Gradual Migration

1. **Build new app shell** (Next.js + auth)
2. **Migrate one feature at a time**:
   - Week 1: Dashboard (scan list)
   - Week 2: Repository management
   - Week 3: Scan results (basic view)
   - Week 4: Graph visualization (React Flow)
   - Week 5: Database schema view
   - Week 6: Filters & exports
3. **Run both in parallel** (feature flag)
4. **Sunset Streamlit** after 90% adoption

### Phase 3: Full Next.js App

**Replace Streamlit visualization with**:
- **React Flow** for workflow graphs
- **D3.js** for complex diagrams
- **Recharts/Visx** for charts
- **Mermaid.js** (keep this - it works great!)

---

## 💰 Cost Estimates

### Startup Phase (<100 users)

| Service | Provider | Cost/month |
|---------|----------|------------|
| Frontend Hosting | Vercel | $20 |
| Backend + DB | Railway | $20 |
| Auth | Clerk | Free |
| Payments | Stripe | 2.9% of revenue |
| Email | SendGrid | Free (100/day) |
| Storage | S3 | $5 |
| Monitoring | Sentry | Free |
| **Total** | | **$45-50/month** |

### Growth Phase (100-1,000 users)

| Service | Provider | Cost/month |
|---------|----------|------------|
| Frontend | Vercel Pro | $20 |
| Backend | Railway Starter | $50 |
| Database | Railway Postgres | $25 |
| Redis | Railway | $10 |
| Auth | Clerk Pro | $25 |
| Payments | Stripe | 2.9% |
| Email | SendGrid | $20 |
| Storage | S3 | $50 |
| Monitoring | Sentry Team | $26 |
| CDN | Cloudflare | $20 |
| **Total** | | **$246/month** |

### Scale Phase (1,000-10,000 users)

| Service | Provider | Cost/month |
|---------|----------|------------|
| Frontend | Vercel Enterprise | $150 |
| Backend | AWS ECS | $300 |
| Database | AWS RDS | $200 |
| Cache | ElastiCache | $100 |
| Auth | Auth0 | $240 |
| Payments | Stripe | 2.9% |
| Email | SendGrid | $100 |
| Storage | S3 | $200 |
| Monitoring | Datadog | $200 |
| CDN | CloudFront | $100 |
| **Total** | | **$1,590/month** |

---

## 🎯 Recommended Implementation Roadmap

### Month 1-2: Foundation
- [ ] Set up Next.js + FastAPI skeleton
- [ ] Implement auth (Clerk)
- [ ] Build basic database schema
- [ ] Create dashboard shell
- [ ] Integrate Stripe (checkout + webhooks)

### Month 3-4: Core Features
- [ ] Repository management CRUD
- [ ] Scan triggering (background jobs)
- [ ] Basic scan results view (iframe Streamlit)
- [ ] User settings & profile
- [ ] Organization/team management

### Month 5-6: Enhanced UX
- [ ] Migrate visualizations to React Flow
- [ ] Build custom database schema view
- [ ] Add filtering & search
- [ ] Implement API for CLI tool
- [ ] Create onboarding flow

### Month 7-8: Integrations
- [ ] Confluence integration UI
- [ ] CI/CD webhook endpoints
- [ ] Slack notifications
- [ ] Email reports
- [ ] API documentation (Swagger)

### Month 9-10: Enterprise Features
- [ ] SSO/SAML (Auth0 upgrade)
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Custom branding
- [ ] SLA monitoring

### Month 11-12: Scale & Polish
- [ ] Performance optimization
- [ ] SOC2 compliance prep
- [ ] Mobile responsive design
- [ ] Advanced analytics
- [ ] White-label option

---

## 🚀 Conclusion

**Recommended Stack Summary**:
- **Frontend**: Next.js + React + TypeScript + Tailwind
- **Backend**: FastAPI + PostgreSQL + Redis + Celery
- **Auth**: Clerk (early) → Auth0 (enterprise)
- **Payments**: Stripe
- **Hosting**: Vercel (frontend) + Railway (backend)
- **Storage**: AWS S3 or Cloudflare R2
- **Monitoring**: Sentry + Datadog

**Why This Stack**:
- ✅ Proven at scale (used by thousands of SaaS companies)
- ✅ Fast to develop (leverage existing tools)
- ✅ Easy to hire for (popular technologies)
- ✅ Cost-effective ($45-250/month for first 1,000 users)
- ✅ Enterprise-ready (can scale to millions)

**Next Steps**:
1. Validate revenue model (see REVENUE_STRATEGY.md)
2. Build landing page + waitlist
3. Get 5 pilot customers ($0 or deeply discounted)
4. Use feedback to prioritize features
5. Start with MVP: auth + billing + basic scan view
6. Iterate based on usage data

---

**Document Version**: 1.0
**Last Updated**: October 31, 2025
**Author**: Claude (AI Assistant)
**Status**: Technical Specification - Ready for Implementation
