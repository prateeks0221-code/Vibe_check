# Rule 08: Deployment & Infrastructure

## Current State: Native macOS

The stack runs natively on macOS with Homebrew. No Docker. This is intentional for rapid iteration.

## Future Path: Docker Compose

The repo already contains Dockerfiles and `docker-compose.yml`. They are **not actively maintained** but serve as the production target.

When moving to Docker:

1. Update `docker-compose.yml` to use the actual Docker daemon
2. Build images: `docker compose build`
3. Run: `docker compose up`

## Production Checklist (Post-MVP)

- [ ] Replace SQLite with PostgreSQL
- [ ] Add Alembic for migrations
- [ ] Add Redis persistence or replace with RabbitMQ
- [ ] Add nginx reverse proxy in front of FastAPI
- [ ] Use S3/MinIO for HLS segment storage instead of local filesystem
- [ ] Add Prometheus metrics endpoint
- [ ] Add structured logging (JSON) to stdout
- [ ] Add health checks for each service
- [ ] Add CI/CD (GitHub Actions: lint, test, build, deploy)
- [ ] Secrets management (HashiCorp Vault or AWS Secrets Manager)
- [ ] TLS termination at load balancer
- [ ] Rate limiting on API endpoints

## Environment-Specific Configs

| Env | Database | Redis | HLS | Notes |
|-----|----------|-------|-----|-------|
| Local dev | SQLite | local | Python HTTP server | `./start-demo.sh` |
| Staging | PostgreSQL | Redis Cloud | S3/CloudFront | Docker Compose |
| Production | PostgreSQL | Redis Cluster | CDN + S3 | Kubernetes |

## Scaling the CV Pipeline

Current: one Python process reads all venues sequentially.

Future: shard by venue_id. Each worker handles N venues:

```bash
# Worker 1: venues 001-050
VENUE_SHARD=0-50 python cv-pipeline/src/main.py

# Worker 2: venues 051-100
VENUE_SHARD=51-100 python cv-pipeline/src/main.py
```

## Scaling the HLS Layer

Current: one ffmpeg per venue, one Python HTTP server.

Future: use MediaMTX's native HLS (`:8888`) or a CDN origin pull from S3.

## Secrets

Never commit secrets. Use `.env` files (gitignored):

```bash
# .env
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379/0
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=yyy
```

Load with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```
