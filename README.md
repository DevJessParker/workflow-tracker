# 🪅 Pinata Code

> *It's what's inside that counts*

**Pinata Code** is transforming from a standalone workflow analysis tool into a **production-ready, multi-tenant SaaS platform** for code workflow analysis and visualization.

## 🚀 New: Production SaaS Platform

This repository now contains a **complete monorepo structure** ready for production deployment:

- 🎨 **React + Next.js 14** frontend (TypeScript + Tailwind CSS)
- ⚡ **FastAPI + Python** backend (SQLAlchemy + Celery)
- 🔍 **Existing scanning engine** (preserved and enhanced)
- 🐳 **Docker Compose** for local development
- 💳 **Stripe billing** integration ready
- 🔐 **Clerk.dev authentication** ready
- 📊 **Multi-tenant architecture** with organizations & teams

### Quick Links

- 📖 **[QUICKSTART.md](QUICKSTART.md)** - Start building the production SaaS
- 📋 **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md)** - 12-week roadmap
- 💰 **[Revenue Strategy](docs/REVENUE_STRATEGY.md)** - Business model & pricing
- 🏗️ **[Architecture](docs/ARCHITECTURE_SCALABLE_SAAS.md)** - Technical deep dive

### Project Structure

```
pinata-code/
├── frontend/              # Next.js 14 + React + TypeScript
├── backend/               # FastAPI + SQLAlchemy + Celery
├── scanner/               # Python scanning engine (existing code)
├── infrastructure/        # Docker Compose + deployment configs
├── docs/                  # Comprehensive documentation
└── QUICKSTART.md          # Get started guide
```

### Revenue Model

- **Free**: 1 repository, 10 scans/month
- **Team ($49/mo)**: 10 repos, 1,000 scans/month
- **Enterprise ($499/mo)**: Unlimited repos & scans

---

## 🎯 What Can You Do?

### For Building the SaaS Platform

**Start here:** Read **[QUICKSTART.md](QUICKSTART.md)** to get Docker Compose running and begin development.

**Then follow:** The **[12-week implementation plan](docs/IMPLEMENTATION_PLAN.md)** for the complete roadmap.

### For Using the Scanner

The workflow scanner is now fully integrated into the web application! See **[SCANNER_INTEGRATION.md](SCANNER_INTEGRATION.md)** for:
- Accessing the scanner at `/dashboard/scanner`
- Scanning local and cloud repositories
- Viewing real-time workflow visualizations
- Exporting Mermaid diagrams

---

## 📊 Core Features

### Code Analysis
- **Multi-language scanning**: C#, TypeScript, JavaScript
- **Pattern detection**: Database operations, API calls, file I/O, message queues
- **Static analysis**: No runtime execution required
- **Incremental scanning**: Only scan changed files (planned)

### Visualization
- Interactive workflow graphs (React Flow)
- Database schema diagrams (Mermaid)
- Operations analytics (Plotly charts)
- Real-time progress tracking

### Multi-Tenancy
- Organization & team management
- Role-based access control
- Usage tracking & quotas
- Subscription billing (Stripe)

### Integrations
- **Git**: GitHub, GitLab webhooks
- **Auth**: Clerk.dev SSO
- **Storage**: S3-compatible object storage
- **Legacy**: Confluence publishing (scanner tool)

---

## 📁 Repository Structure

```
pinata-code/
├── frontend/              # Next.js 14 + React + TypeScript
│   ├── app/              # Next.js app router
│   ├── components/       # React components
│   └── lib/              # Utilities
├── backend/              # FastAPI + SQLAlchemy
│   ├── app/              # Application code
│   │   ├── api/         # REST endpoints
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── tasks/       # Celery jobs
│   └── tests/           # Test suite
├── scanner/              # Python scanning engine
│   ├── scanner/         # Core scanning logic
│   ├── graph/           # Visualization generation
│   ├── deprecated/      # Archived Streamlit app
│   └── integrations/    # Confluence, etc.
├── infrastructure/       # Docker & deployment
│   └── docker/          # docker-compose.yml
├── docs/                # Documentation
│   ├── IMPLEMENTATION_PLAN.md
│   ├── REVENUE_STRATEGY.md
│   └── ARCHITECTURE_SCALABLE_SAAS.md
└── QUICKSTART.md        # Getting started guide
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui
- **State**: Zustand
- **Data Fetching**: React Query

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Queue**: Celery
- **Storage**: S3/MinIO

### Scanning Engine
- **Language**: Python 3.11
- **Parsing**: Tree-sitter, Regex
- **Analysis**: Static code analysis
- **Output**: Mermaid, JSON, HTML

---

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 60 seconds with Docker Compose
- **[SCANNER_INTEGRATION.md](SCANNER_INTEGRATION.md)** - How to use the integrated scanner
- **[docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)** - 12-week development roadmap
- **[docs/REVENUE_STRATEGY.md](docs/REVENUE_STRATEGY.md)** - Business model & pricing
- **[docs/ARCHITECTURE_SCALABLE_SAAS.md](docs/ARCHITECTURE_SCALABLE_SAAS.md)** - Technical architecture
- **[backend/README.md](backend/README.md)** - Backend development guide
- **[frontend/README.md](frontend/README.md)** - Frontend development guide
- **[scanner/README.md](scanner/README.md)** - Scanning engine details
- **[infrastructure/README.md](infrastructure/README.md)** - Docker & deployment

---

## 🚀 Development Roadmap

| Phase | Timeline | Status |
|-------|----------|--------|
| **Foundation** | Weeks 1-2 | ✅ Structure ready |
| **Core Features** | Weeks 3-6 | 📋 Planned |
| **Billing** | Weeks 7-8 | 📋 Planned |
| **Testing** | Weeks 9-10 | 📋 Planned |
| **Deployment** | Weeks 11-12 | 📋 Planned |

**Current Status**: Monorepo foundation complete. Ready for Phase 1 implementation.

---

## 💰 Business Model

### Pricing Tiers
- **Free**: 1 repository, 10 scans/month - Perfect for individuals
- **Team**: $49/month, 10 repos, 1,000 scans/month - For small teams
- **Enterprise**: $499/month, unlimited - For organizations

### Revenue Projections
- **Year 1**: $100K-250K ARR target
- **Year 2**: $250K-500K ARR target
- **Year 3**: $500K-1M ARR target

See **[docs/REVENUE_STRATEGY.md](docs/REVENUE_STRATEGY.md)** for detailed analysis.

---

## 🤝 Contributing

Pinata Code is in active development. Contributions welcome!

**For the SaaS platform:**
1. Read the [implementation plan](docs/IMPLEMENTATION_PLAN.md)
2. Check current phase progress
3. Pick a task from the roadmap
4. Submit a pull request

**For the scanning engine:**
1. See [scanner/README.md](scanner/README.md)
2. Add language support or new patterns
3. Submit a pull request

---

## 📄 License

Proprietary - Part of Pinata Code SaaS Platform

---

**Ready to start?** Open **[QUICKSTART.md](QUICKSTART.md)** and let's build! 🪅
