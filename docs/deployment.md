# AVOM Production Deployment & Infrastructure Guide

This guide details architecture options, environment configurations, and operational runbooks for deploying **AVOM** into staging and production environments.

---

## 1. Production Architecture Overview

AVOM employs a modular, cloud-agnostic architecture allowing components to be deployed either together via containers or decoupled into managed cloud services:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Web & Mobile Clients                     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Reverse Proxy / CDN (Vercel / Nginx)            │
│               - Static SPA Bundle Caching                   │
│               - SSL/TLS Termination                         │
└──────────────┬──────────────────────────────┬───────────────┘
               │ /                            │ /api/*
               ▼                              ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│      React 18 Frontend       │ │       FastAPI Backend       │
│      (Vite SPA Dist)         │ │   (Gunicorn / Uvicorn)      │
└──────────────────────────────┘ └──────────────┬──────────────┘
                                                │
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         ▼                                      ▼                                      ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│      Managed PostgreSQL      │ │        Qdrant Cloud         │ │        Managed Redis        │
│   (Neon / Supabase / RDS)    │ │   (Vector Similarity)       │ │     (Upstash / ElastiCache) │
│ - Users, Projects, Metadata  │ │ - HNSW Cosine Indexing      │ │ - Task Broker & Rate Limits │
│ - Evaluation Runs & Traces   │ │ - Tenant Filtering          │ │ - Session & Query Caching   │
└──────────────────────────────┘ └─────────────────────────────┘ └─────────────────────────────┘
```

---

## 2. Deployment Architecture Options

### Option A: Fully Managed Cloud PaaS (Recommended for Rapid Launch)

| Component | Recommended Provider | Alternative | Configuration Notes |
|---|---|---|---|
| **Frontend** | [Vercel](https://vercel.com) | Cloudflare Pages, Netlify | Connect Git repo, set root directory to `apps/frontend`, build command `npm run build`, output directory `dist`. Add rewrite rule for `/api/:path*` to backend URL. |
| **Backend API** | [Render](https://render.com) | Railway, Fly.io, AWS App Runner | Deploy from Dockerfile (`apps/backend/Dockerfile`). Set environment variables for DB, Qdrant, and Redis. |
| **Relational DB** | [Neon PostgreSQL](https://neon.tech) | Supabase, AWS RDS | Serverless Postgres with instant branching. Provide `postgresql+asyncpg://...` connection string. |
| **Vector DB** | [Qdrant Cloud](https://cloud.qdrant.io) | Self-hosted Qdrant | Create a managed cluster. Configure `QDRANT_URL` and `QDRANT_API_KEY`. |
| **Redis** | [Upstash Redis](https://upstash.com) | Redis Cloud | Serverless Redis with sub-millisecond response times. |

---

### Option B: Single VM / VPS with Docker Compose (Cost Effective)

Deployable on any Linux VPS (Ubuntu 22.04 LTS on Hetzner, DigitalOcean, Linode, or AWS EC2 `t3.medium` or higher):

1. **Clone Repository & Provision Environment**:
   ```bash
   git clone https://github.com/your-org/avom.git
   cd avom
   cp .env.example .env.production
   ```

2. **Configure Production Variables** in `.env.production`:
   ```bash
   POSTGRES_USER=avom_admin
   POSTGRES_PASSWORD=<STRONG_RANDOM_PASSWORD>
   POSTGRES_DB=avom_production
   JWT_SECRET_KEY=<SECURE_64_CHAR_HEX_KEY>
   ENVIRONMENT=production
   DEBUG=false
   OPENAI_API_KEY=sk-...
   ```

3. **Launch Stack**:
   ```bash
   docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
   ```

4. **Verify Health**:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   curl -s http://localhost:8000/api/v1/health/readiness
   ```

---

## 3. Database Migration Runbook (Alembic)

Database schema evolution is managed via Alembic async migrations located in `apps/backend/alembic/`.

### Running Migrations in Production:
```bash
cd apps/backend
# Execute pending upgrades up to HEAD
alembic upgrade head
```

### Checking Current Migration Status:
```bash
alembic current
alembic history --verbose
```

### Rolling Back a Migration:
```bash
alembic downgrade -1
```

---

## 4. Environment Variables Specification

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Yes | `sqlite+aiosqlite:///./avom_dev.db` | PostgreSQL async connection string (`postgresql+asyncpg://user:pass@host:5432/db`) |
| `QDRANT_HOST` | No | `localhost` | Qdrant vector engine host |
| `QDRANT_PORT` | No | `6333` | Qdrant HTTP/REST port |
| `QDRANT_API_KEY` | No | `""` | Qdrant Cloud cluster authorization key |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis caching and task broker endpoint |
| `JWT_SECRET_KEY` | Yes | `test-secret-key-change-in-production` | HS256 secret key for signing user authentication tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `10080` (7 days) | JWT expiration duration in minutes |
| `OPENAI_API_KEY` | Optional | `""` | OpenAI API key for `text-embedding-3-small` and `gpt-4o-mini` |
| `GEMINI_API_KEY` | Optional | `""` | Google Gemini API key for `gemini-1.5-flash` synthesis |
| `ENVIRONMENT` | No | `production` | `development`, `testing`, or `production` |
| `DEBUG` | No | `false` | Enables verbose stack traces when set to `true` |

---

## 5. Security & Hardening Checklist

- [x] **OWASP Security Headers**: `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Strict-Transport-Security` applied across all API endpoints.
- [x] **Rate Limiting**: Sliding window rate limiter prevents denial-of-service and brute-force token generation.
- [x] **Tenant Workspace Isolation**: Document chunks and vector lookups are strictly partitioned by `project_id`.
- [x] **Correlation Tracking**: Every request generates an `X-Request-ID` logged alongside execution latency.
- [x] **Password Hashing**: Industry-standard `bcrypt` password hashing with salt.
- [x] **Zero Mock Fallbacks**: Local deterministic retrieval, cross-encoding, and LLM synthesis provide 100% offline functionality.

---

## 6. Backup & Disaster Recovery

### PostgreSQL Automated Backup:
```bash
# Nightly logical dump
docker exec -t avom_prod_postgres pg_dump -U avom_admin avom_production | gzip > /backups/avom_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Qdrant Collection Snapshot:
```bash
# Trigger Qdrant snapshot via REST API
curl -X POST "http://localhost:6333/collections/avom_chunks/snapshots"
```
