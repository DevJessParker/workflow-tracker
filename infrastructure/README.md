# Pinata Code - Infrastructure

This directory contains infrastructure configuration for development, testing, and production deployments.

## Structure

```
infrastructure/
├── docker/
│   ├── docker-compose.yml       # Development environment
│   ├── docker-compose.prod.yml  # Production environment
│   └── docker-compose.test.yml  # Test environment (TODO)
├── kubernetes/                  # K8s manifests (future)
│   ├── deployments/
│   ├── services/
│   └── ingress/
├── terraform/                   # IaC for cloud resources (future)
│   ├── aws/
│   └── modules/
└── nginx/                       # Nginx configuration (TODO)
    ├── nginx.conf
    └── ssl/
```

## Docker Compose

### Development Environment

Start all services for local development:

```bash
cd infrastructure/docker
docker-compose up
```

Services:
- **Frontend**: http://localhost:3000 (Next.js with hot reload)
- **Backend**: http://localhost:8000 (FastAPI with auto-reload)
- **Database**: localhost:5432 (PostgreSQL)
- **Redis**: localhost:6379
- **MinIO**: http://localhost:9000 (S3-compatible storage)
- **MinIO Console**: http://localhost:9001
- **PgAdmin**: http://localhost:5050 (optional, dev-tools profile)

```bash
# Start with PgAdmin
docker-compose --profile dev-tools up

# Start specific services
docker-compose up backend db redis

# Stop all services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

### Production Environment

```bash
cd infrastructure/docker
docker-compose -f docker-compose.prod.yml up -d
```

Production features:
- Multi-replica backend and workers
- Nginx reverse proxy with SSL
- Optimized resource limits
- Gunicorn for backend (production WSGI)
- Health checks and restarts

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# From project root
cp .env.example .env
nano .env  # Edit configuration
```

## Docker Images

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev

# Copy application
COPY app/ ./app/
COPY alembic/ ./alembic/

# Run migrations and start server
CMD poetry run alembic upgrade head && \
    poetry run gunicorn app.main:app --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./

RUN npm ci --production

EXPOSE 3000
CMD ["npm", "start"]
```

## Kubernetes (Future - Phase 3+)

For production scale-out deployment:

```yaml
# kubernetes/deployments/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pinata-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pinata-backend
  template:
    metadata:
      labels:
        app: pinata-backend
    spec:
      containers:
      - name: backend
        image: pinata-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: pinata-secrets
              key: database-url
```

## Terraform (Future - Phase 3+)

Infrastructure as Code for AWS deployment:

```hcl
# terraform/aws/main.tf
resource "aws_ecs_cluster" "pinata" {
  name = "pinata-production"
}

resource "aws_ecs_service" "backend" {
  name            = "pinata-backend"
  cluster         = aws_ecs_cluster.pinata.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 3
}
```

## Monitoring

### Development

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Production

- **Sentry**: Error tracking and performance monitoring
- **Datadog**: APM, infrastructure monitoring
- **CloudWatch**: AWS logs and metrics
- **PostHog**: Product analytics

## Scaling

### Vertical Scaling (Single Server)

Edit `docker-compose.prod.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '4'    # Increase CPU
        memory: 4G   # Increase memory
```

### Horizontal Scaling (Multiple Servers)

```yaml
backend:
  deploy:
    replicas: 5  # Increase replicas
```

### Database Scaling

For high traffic:
- Enable PostgreSQL connection pooling (PgBouncer)
- Add read replicas
- Consider managed database (RDS, Aurora)

## Backup & Recovery

### Database Backups

```bash
# Manual backup
docker-compose exec db pg_dump -U postgres pinata_dev > backup.sql

# Restore
docker-compose exec -T db psql -U postgres pinata_dev < backup.sql

# Automated backups (cron)
0 2 * * * docker-compose exec db pg_dump -U postgres pinata_dev | gzip > /backups/pinata_$(date +\%Y\%m\%d).sql.gz
```

### S3 Backups

Configure MinIO/S3 versioning and lifecycle policies.

## Security

### Secrets Management

Never commit secrets! Use:
- `.env` files (gitignored)
- Docker secrets (production)
- AWS Secrets Manager (production)
- Vault (enterprise)

### Network Security

Production setup:
- Nginx reverse proxy with SSL
- Firewall rules (only expose 80/443)
- VPC for backend services (AWS)
- WAF for DDoS protection

### SSL Certificates

```bash
# Let's Encrypt with Certbot
certbot certonly --standalone -d api.pinatacode.com

# Copy to nginx
cp /etc/letsencrypt/live/api.pinatacode.com/fullchain.pem infrastructure/nginx/ssl/
cp /etc/letsencrypt/live/api.pinatacode.com/privkey.pem infrastructure/nginx/ssl/
```

## Deployment Checklist

- [ ] Set all environment variables in `.env`
- [ ] Update `CORS_ORIGINS` with production domain
- [ ] Configure Clerk.dev with production domain
- [ ] Configure Stripe with production keys
- [ ] Set up SSL certificates
- [ ] Configure Sentry DSN
- [ ] Run database migrations
- [ ] Create S3 bucket
- [ ] Set up backups
- [ ] Configure monitoring
- [ ] Test health checks
- [ ] Load test with realistic traffic

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Check container status
docker-compose ps

# Rebuild image
docker-compose build --no-cache backend
```

### Database connection failed

```bash
# Check if DB is ready
docker-compose exec db pg_isready -U postgres

# Check connection string
docker-compose exec backend env | grep DATABASE_URL
```

### Port already in use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

## Cost Estimation

### Development (Local)
- **Cost**: $0
- **Resources**: Developer machine

### Phase 1-2 (Railway.app)
- **Cost**: $50-150/month
- **Services**: Web, worker, PostgreSQL, Redis

### Phase 3+ (AWS ECS)
- **Cost**: $400-2,000/month
- **Services**: ECS, RDS, ElastiCache, S3, CloudWatch

See `../docs/ARCHITECTURE_SCALABLE_SAAS.md` for detailed cost breakdown.

## Next Steps

1. ✅ Create Docker Compose configurations
2. ⏳ Create Dockerfiles for backend/frontend
3. ⏳ Set up GitHub Actions for CI/CD
4. ⏳ Configure production environment
5. ⏳ Set up monitoring and alerts

See `../docs/IMPLEMENTATION_PLAN.md` for detailed roadmap.

## License

Part of Pinata Code - Proprietary Software
