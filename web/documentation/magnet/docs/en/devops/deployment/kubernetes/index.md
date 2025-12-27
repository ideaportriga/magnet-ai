# Kubernetes/OpenShift Deployment

Deploy Magnet AI to Kubernetes or OpenShift by running the Magnet AI container image and connecting it to a PostgreSQL database with `pgvector` enabled.

> Note: this repository does not currently ship ready-made Kubernetes/OpenShift manifests. Use the examples below as a starting point for your cluster standards (Ingress, TLS, managed PostgreSQL, etc.).

## Prerequisites

- Kubernetes or OpenShift cluster access
- CLI installed (`kubectl` or `oc`)
- Network/registry access to pull `ghcr.io/ideaportriga/magnet-ai:latest` (and credentials if your cluster requires it)
- PostgreSQL with `pgvector` enabled (managed database recommended)

## Database (pgvector)

This guide assumes you already have a PostgreSQL database available and reachable from the cluster.

- **Managed PostgreSQL (recommended)**: simplest operationally (backups, HA, upgrades handled by the cloud provider).
- **In-cluster PostgreSQL**: possible via an operator or a StatefulSet, but **database installation is out of scope** for this guide.

Whichever option you choose, ensure `pgvector` is enabled:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Deployment Steps

### 1. Use the published Magnet AI image

```bash
# Use the published image:
IMAGE="ghcr.io/ideaportriga/magnet-ai:latest"
```

### 2. Create Namespace / Project

```bash
kubectl create namespace magnet-ai
# OpenShift: oc new-project magnet-ai
```

> Optional: if you need credentials to pull from `ghcr.io`, create an image pull secret and reference it in the Pod spec.

```bash
kubectl -n magnet-ai create secret docker-registry ghcr-cred \
  --docker-server=ghcr.io \
  --docker-username="<github-username>" \
  --docker-password="<github-token>" \
  --docker-email="<email>"
```

### 3. Configure Environment (Secrets/ConfigMaps)

At minimum, configure database connectivity and `SECRET_ENCRYPTION_KEY` (used to encrypt/decrypt secrets stored in the database).

```bash
# Example: store configuration as a Secret (adjust to your security standards)
# Replace DB_HOST/DB_PASSWORD with your database endpoint/secret.
# If you run Postgres in-cluster and expose a Service named "magnet-postgres", you can use DB_HOST=magnet-postgres.
kubectl -n magnet-ai create secret generic magnet-env \
  --from-literal=ENV=production \
  --from-literal=PORT=5000 \
  --from-literal=WEB_INCLUDED=true \
  --from-literal=AUTH_ENABLED=true \
  --from-literal=CORS_OVERRIDE_ALLOWED_ORIGINS=https://yourdomain.com \
  --from-literal=DB_TYPE=postgresql \
  --from-literal=DB_HOST=your-postgres-host \
  --from-literal=DB_PORT=5432 \
  --from-literal=DB_NAME=magnet_prod \
  --from-literal=DB_USER=magnet \
  --from-literal=DB_PASSWORD=strong-password-here \
  --from-literal=SECRET_ENCRYPTION_KEY=generate-strong-secret-key
```

### 4. Deploy Magnet AI (example YAML)

Create `magnet-ai.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: magnet-ai
  namespace: magnet-ai
spec:
  replicas: 1
  selector:
    matchLabels:
      app: magnet-ai
  template:
    metadata:
      labels:
        app: magnet-ai
    spec:
      # Uncomment if you created the ghcr-cred pull secret
      # imagePullSecrets:
      #   - name: ghcr-cred
      containers:
        - name: magnet-ai
          image: ghcr.io/ideaportriga/magnet-ai:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 5000
          envFrom:
            - secretRef:
                name: magnet-env
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 20
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: magnet-ai
  namespace: magnet-ai
spec:
  selector:
    app: magnet-ai
  ports:
    - name: http
      port: 80
      targetPort: 5000
```

```bash
kubectl apply -f magnet-ai.yaml
```

### 5. Expose the Service

- **Kubernetes (Ingress)**: create an Ingress that routes `/` to `service/magnet-ai` (port 80).
- **OpenShift (Route)**: expose the service:

```bash
oc -n magnet-ai expose service/magnet-ai --hostname=magnet.yourdomain.com
```

### 6. Verify

```bash
kubectl -n magnet-ai get pods
kubectl -n magnet-ai port-forward svc/magnet-ai 8080:80
```

Open:

- `http://localhost:8080/admin/`
- `http://localhost:8080/panel/`
- `http://localhost:8080/help/`

### 7. Updates (pull latest image)

Because this guide uses the `:latest` tag, updating typically means restarting the Deployment to force a new pull:

```bash
kubectl -n magnet-ai rollout restart deployment/magnet-ai
```