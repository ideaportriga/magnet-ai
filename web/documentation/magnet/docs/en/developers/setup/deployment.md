# Deployment

Guide for deploying Magnet AI to production environments.

## Deployment Options

### 1. Docker Deployment (Recommended)
### 2. Manual Deployment
### 3. OpenShift/Kubernetes
### 4. Cloud Platforms (AWS, Azure, GCP)

## Docker Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ disk space

### Quick Deploy

#### Using Docker Compose

```bash
# Clone repository
git clone https://github.com/yourusername/magnet-ai.git
cd magnet-ai

# Configure environment
cp .env.example .env
# Edit .env with production values

# Start services
docker-compose up -d
```

Services:
- **API**: `http://localhost:5000`
- **Web**: `http://localhost:80`
- **PostgreSQL**: `localhost:5432`

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: magnet_prod
      POSTGRES_USER: magnet
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://magnet:${DB_PASSWORD}@postgres:5432/magnet_prod
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
      FLASK_ENV: production
    depends_on:
      - postgres
    restart: always

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
      args:
        VITE_API_URL: https://api.yourdomain.com
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: always

volumes:
  postgres_data:
```

Deploy:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Configuration

Create `.env`:

```bash
# Database
DB_PASSWORD=strong-password-here

# OpenAI
OPENAI_API_KEY=sk-your-production-key

# Application
SECRET_KEY=generate-strong-secret-key
FLASK_ENV=production
DEBUG=False

# CORS
CORS_ORIGINS=https://yourdomain.com

# Optional
VECTOR_DB_URL=...
REDIS_URL=...
```

### SSL/TLS Configuration

#### Using Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/
```

#### Nginx Configuration

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://api:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Manual Deployment

### Backend Deployment

#### 1. Prepare Server

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade

# Install dependencies
sudo apt-get install python3.12 python3-pip postgresql nginx
```

#### 2. Set Up Application

```bash
# Clone repository
git clone https://github.com/yourusername/magnet-ai.git
cd magnet-ai/api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure Database

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE magnet_prod;
CREATE USER magnet WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE magnet_prod TO magnet;
\q

# Run migrations
python scripts/ensure_database.py
```

#### 4. Configure Environment

```bash
# Create .env
cat > .env << EOF
DATABASE_URL=postgresql://magnet:password@localhost/magnet_prod
OPENAI_API_KEY=sk-your-key
SECRET_KEY=your-secret-key
FLASK_ENV=production
EOF
```

#### 5. Set Up Gunicorn

Install:

```bash
pip install gunicorn
```

Create `gunicorn.conf.py`:

```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "/var/log/magnet/access.log"
errorlog = "/var/log/magnet/error.log"
```

Run:

```bash
gunicorn -c gunicorn.conf.py "src.app:create_app()"
```

#### 6. Set Up Systemd Service

Create `/etc/systemd/system/magnet-api.service`:

```ini
[Unit]
Description=Magnet AI API
After=network.target

[Service]
User=magnet
WorkingDirectory=/home/magnet/magnet-ai/api
Environment="PATH=/home/magnet/magnet-ai/api/venv/bin"
ExecStart=/home/magnet/magnet-ai/api/venv/bin/gunicorn -c gunicorn.conf.py "src.app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable magnet-api
sudo systemctl start magnet-api
sudo systemctl status magnet-api
```

### Frontend Deployment

#### 1. Build Frontend

```bash
cd web
npm install
npm run build:knowledge-magnet
```

Build output: `dist/apps/knowledge-magnet`

#### 2. Deploy to Nginx

```bash
# Copy build files
sudo cp -r dist/apps/knowledge-magnet/* /var/www/magnet/

# Configure Nginx
sudo nano /etc/nginx/sites-available/magnet
```

Nginx config:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    root /var/www/magnet;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/magnet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## OpenShift Deployment

Magnet AI includes OpenShift deployment configurations.

### Prerequisites

- OpenShift cluster access
- OpenShift CLI (`oc`) installed
- Container registry access

### Deployment Steps

#### 1. Build Images

```bash
# Build API image
cd api
docker build -t your-registry/magnet-ai-api:latest .
docker push your-registry/magnet-ai-api:latest

# Build Web image
cd ../web
docker build -t your-registry/magnet-ai-web:latest .
docker push your-registry/magnet-ai-web:latest
```

#### 2. Create Project

```bash
oc new-project magnet-ai
```

#### 3. Create Secrets

```bash
# Create secrets from file
oc create secret generic magnet-secrets \
  --from-file=secrets.env

# Or from literals
oc create secret generic magnet-secrets \
  --from-literal=DATABASE_URL=postgresql://... \
  --from-literal=OPENAI_API_KEY=sk-...
```

#### 4. Deploy

```bash
cd openshift
oc apply -f Deployment.yml
```

See `openshift/README.md` for detailed instructions.

## Cloud Platforms

### AWS

#### Using ECS (Elastic Container Service)

1. Push images to ECR
2. Create ECS cluster
3. Define task definitions
4. Create services
5. Configure load balancer

#### Using Elastic Beanstalk

1. Create application
2. Upload Docker Compose file
3. Configure environment
4. Deploy

### Azure

#### Using Container Apps

```bash
az containerapp up \
  --name magnet-ai \
  --resource-group magnet-rg \
  --location eastus \
  --image your-registry/magnet-ai:latest \
  --target-port 80 \
  --ingress external
```

### Google Cloud Platform

#### Using Cloud Run

```bash
gcloud run deploy magnet-ai \
  --image gcr.io/your-project/magnet-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Database Migration

### Backup

```bash
# PostgreSQL backup
pg_dump magnet_prod > backup.sql

# Restore
psql magnet_prod < backup.sql
```

### Migrations

```bash
cd api
python manage_migrations.py upgrade
```

## Monitoring

### Application Logs

```bash
# Docker logs
docker-compose logs -f api

# Systemd logs
sudo journalctl -u magnet-api -f
```

### Health Checks

```bash
# API health
curl http://localhost:5000/api/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

### Monitoring Tools

- **Prometheus**: Metrics collection
- **Grafana**: Visualization (see `LOGGING.md`)
- **Sentry**: Error tracking
- **New Relic**: APM

## Security Checklist

- [ ] Use HTTPS/TLS
- [ ] Set strong SECRET_KEY
- [ ] Enable CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable rate limiting
- [ ] Keep dependencies updated
- [ ] Regular security audits
- [ ] Backup database regularly
- [ ] Monitor logs for anomalies
- [ ] Use firewall rules

## Performance Optimization

### Backend

- Use production WSGI server (Gunicorn)
- Enable caching
- Optimize database queries
- Use connection pooling
- Scale horizontally

### Frontend

- Enable gzip compression
- Use CDN for static assets
- Optimize images
- Code splitting
- Browser caching

### Database

- Create indexes
- Regular VACUUM
- Connection pooling
- Read replicas for scaling

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  api:
    deploy:
      replicas: 3
```

```bash
docker-compose -f docker-compose.scale.yml up -d --scale api=3
```

### Load Balancing

Use Nginx or cloud load balancer to distribute traffic.

## Troubleshooting

### Common Issues

**Issue**: Database connection refused
- Check DATABASE_URL
- Verify database is running
- Check network connectivity

**Issue**: CORS errors
- Verify CORS_ORIGINS setting
- Check request headers
- Ensure frontend URL is whitelisted

**Issue**: High memory usage
- Increase worker processes
- Check for memory leaks
- Optimize queries

## Next Steps

- [Getting Started](/docs/en/developers/setup/getting-started) - Development setup
- [Testing](/docs/en/developers/setup/testing) - Testing guide
- [System Architecture](/docs/en/developers/architecture/system-architecture) - Architecture overview
