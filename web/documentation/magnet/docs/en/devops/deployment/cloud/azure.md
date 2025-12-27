# Azure Deployment

Deploy Magnet AI on Azure using:

- **Azure Container Apps**: runs the Magnet AI container (API + Admin/Panel + Help docs)
- **Azure Database for PostgreSQL**: application database (with `pgvector`)
- **GitHub Container Registry (GHCR)**: pulls `ghcr.io/ideaportriga/magnet-ai:latest`

## Prerequisites

- Azure subscription + `az` CLI (v2.81.0+)
- `psql` client (to enable `vector` / `pgcrypto` extensions)

## 1. Set variables

```bash
RG="magnet-rg"
LOCATION="westeurope"

APP_NAME="magnet-ai"
ENV_NAME="magnet-ai-env"
IMAGE="ghcr.io/ideaportriga/magnet-ai:latest"

# Main DB
PG_SERVER="magnet-pg-123"            # must be globally unique
DB_NAME="magnet"
DB_USER="postgres"
DB_PASSWORD="strong-password-here"

# Key Vault
KEYVAULT_NAME="magnet-kv-123"        # must be globally unique (24 characters max)

# App DB secrets (stored in Key Vault; referenced by the Container App)
KV_SECRET_DB_USER="db-user"
KV_REF_DB_USER="keyvaultref:https://${KEYVAULT_NAME}.vault.azure.net/secrets/${KV_SECRET_DB_USER},identityref:system"

KV_SECRET_DB_PASSWORD="db-password"
KV_REF_DB_PASSWORD="keyvaultref:https://${KEYVAULT_NAME}.vault.azure.net/secrets/${KV_SECRET_DB_PASSWORD},identityref:system"

# Magnet secret encryption key (stored in Key Vault; referenced by the Container App)
KV_SECRET_ENCRYPTION_KEY="secret-encryption-key"
KV_REF_ENCRYPTION_KEY="keyvaultref:https://${KEYVAULT_NAME}.vault.azure.net/secrets/${KV_SECRET_ENCRYPTION_KEY},identityref:system"

# Auth (Microsoft Entra ID) - stored in Key Vault
KV_SECRET_MICROSOFT_ENTRA_ID_TENANT_ID="microsoft-entra-id-tenant-id"
KV_REF_MICROSOFT_ENTRA_ID_TENANT_ID="keyvaultref:https://${KEYVAULT_NAME}.vault.azure.net/secrets/${KV_SECRET_MICROSOFT_ENTRA_ID_TENANT_ID},identityref:system"

KV_SECRET_MICROSOFT_ENTRA_ID_CLIENT_ID="microsoft-entra-id-client-id"
KV_REF_MICROSOFT_ENTRA_ID_CLIENT_ID="keyvaultref:https://${KEYVAULT_NAME}.vault.azure.net/secrets/${KV_SECRET_MICROSOFT_ENTRA_ID_CLIENT_ID},identityref:system"

KV_SECRET_MICROSOFT_ENTRA_ID_CLIENT_SECRET="microsoft-entra-id-client-secret"
KV_REF_MICROSOFT_ENTRA_ID_CLIENT_SECRET="keyvaultref:https://${KEYVAULT_NAME}.vault.azure.net/secrets/${KV_SECRET_MICROSOFT_ENTRA_ID_CLIENT_SECRET},identityref:system"

KV_SECRET_MICROSOFT_ENTRA_ID_REDIRECT_URI="microsoft-entra-id-redirect-uri"
KV_REF_MICROSOFT_ENTRA_ID_REDIRECT_URI="keyvaultref:https://${KEYVAULT_NAME}.vault.azure.net/secrets/${KV_SECRET_MICROSOFT_ENTRA_ID_REDIRECT_URI},identityref:system"

CORS_OVERRIDE_ALLOWED_ORIGINS="https://yourdomain.com"
```

## 2. Create (or reuse) a resource group

If the resource group does **not** exist, create it:

```bash
az group create -n "$RG" -l "$LOCATION"
```

If the resource group **already exists**, reuse it:

```bash
az group show -n "$RG" -o table
LOCATION="$(az group show -n "$RG" --query location -o tsv)"
```

## 3. Create an Azure Key Vault for sensitive configuration

Create a Key Vault:

```bash
az keyvault create \
  -g "$RG" \
  -n "$KEYVAULT_NAME" \
  -l "$LOCATION"
```

Manually add the secrets in the vault (**do not** hardcode them in scripts / docs):

- `db-user`: set to the same value as `DB_USER`
- `db-password`: set to the same value as `DB_PASSWORD` (used for PostgreSQL)
- `secret-encryption-key`: value for Magnet's `SECRET_ENCRYPTION_KEY`
- `microsoft-entra-id-tenant-id`: value for `MICROSOFT_ENTRA_ID_TENANT_ID`
- `microsoft-entra-id-client-id`: value for `MICROSOFT_ENTRA_ID_CLIENT_ID`
- `microsoft-entra-id-client-secret`: value for `MICROSOFT_ENTRA_ID_CLIENT_SECRET`
- `microsoft-entra-id-redirect-uri`: value for `MICROSOFT_ENTRA_ID_REDIRECT_URI`

> Important: this guide intentionally does not include secret values. You must create/fill these secrets manually (Azure Portal → Key Vault → **Secrets** → **Generate/Import**).

## 4. Provision PostgreSQL and enable extensions (`pgvector` + `pgcrypto`)

### 4.1. Create a PostgreSQL server (Flexible Server recommended)

Choose one of the following compute profiles:

- Burstable `Standard_B2s` - more suitable for development and testing

```bash
az postgres flexible-server create \
  -g "$RG" \
  -n "$PG_SERVER" \
  -l "$LOCATION" \
  --sku-name Standard_B2s \
  --tier Burstable \
  --storage-size 32 \
  --admin-user "$DB_USER" \
  --admin-password "$DB_PASSWORD" \
  --version 17 \
  --public-access 0.0.0.0
```

- General Purpose `Standard_D4ds_v5` - minimal recommended compute profile for production

```bash
az postgres flexible-server create \
  -g "$RG" \
  -n "$PG_SERVER" \
  -l "$LOCATION" \
  --sku-name Standard_D4ds_v5 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --admin-user "$DB_USER" \
  --admin-password "$DB_PASSWORD" \
  --version 17 \
  --public-access 0.0.0.0
```

> Note: for production deployments, prefer private networking (VNet integration + private access) instead of public firewall rules.
>
> Private networking quick pointer (high level):
> - Create a delegated subnet for Flexible Server
> - Create/link the Private DNS zone `privatelink.postgres.database.azure.com`
> - Re-run `az postgres flexible-server create` with `--subnet <subnetResourceId>` and `--private-dns-zone <privateDnsZoneResourceId>`

### 4.2. Create the application database

```bash
az postgres flexible-server db create \
  -g "$RG" \
  -s "$PG_SERVER" \
  -d "$DB_NAME"
```

### 4.3. Allowlist extensions and enable them

```bash
az postgres flexible-server parameter set \
  --resource-group "$RG" \
  --server-name "$PG_SERVER" \
  --name azure.extensions \
  --value "vector,pgcrypto"

# If Azure indicates the parameter change requires a restart, restart the server:
# az postgres flexible-server restart --resource-group "$RG" --name "$PG_SERVER"
```

### 4.4. Create the `vector` extension in the application database

Connect to the database with `psql` and run:

```sql
CREATE EXTENSION vector;
```

## 5. Create a Container Apps environment

```bash
az containerapp env create -g "$RG" -n "$ENV_NAME" -l "$LOCATION"
```

## 6. Deploy Magnet AI to Azure Container Apps

### 6.1. Create the app:

```bash
az containerapp create \
  -g "$RG" \
  -n "$APP_NAME" \
  --environment "$ENV_NAME" \
  --image "$IMAGE" \
  --ingress external \
  --target-port 5000 \
  --system-assigned \
  --secrets \
    db-user="$KV_REF_DB_USER" \
    db-password="$KV_REF_DB_PASSWORD" \
    secret-encryption-key="$KV_REF_ENCRYPTION_KEY" \
    microsoft-entra-id-tenant-id="$KV_REF_MICROSOFT_ENTRA_ID_TENANT_ID" \
    microsoft-entra-id-client-id="$KV_REF_MICROSOFT_ENTRA_ID_CLIENT_ID" \
    microsoft-entra-id-client-secret="$KV_REF_MICROSOFT_ENTRA_ID_CLIENT_SECRET" \
    microsoft-entra-id-redirect-uri="$KV_REF_MICROSOFT_ENTRA_ID_REDIRECT_URI" \
  --env-vars \
    PORT=5000 \
    WEB_INCLUDED=true \
    RUN_MIGRATIONS=true \
    DB_TYPE=postgresql \
    DB_HOST="$PG_SERVER.postgres.database.azure.com" \
    DB_PORT=5432 \
    DB_NAME="$DB_NAME" \
    DB_USER=secretref:db-user \
    DB_PASSWORD=secretref:db-password \
    DATABASE_POOL_SIZE=5 \
    DATABASE_MAX_POOL_OVERFLOW=3 \
    DATABASE_POOL_TIMEOUT=60 \
    DATABASE_POOL_RECYCLE=3600 \
    DATABASE_PRE_POOL_PING=true \
    SECRET_ENCRYPTION_KEY=secretref:secret-encryption-key \
    PGVECTOR_HOST="$DB_HOST" \
    PGVECTOR_PORT="$DB_PORT" \
    PGVECTOR_DATABASE="$DB_NAME" \
    PGVECTOR_USER=secretref:db-user \
    PGVECTOR_PASSWORD=secretref:db-password \
    PGVECTOR_POOL_SIZE=5 \
    SCHEDULER_POOL_SIZE=2 \
    SCHEDULER_MAX_POOL_OVERFLOW=0 \
    SCHEDULER_POOL_TIMEOUT=300 \
    SCHEDULER_POOL_RECYCLE=3600 \
    SCHEDULER_POOL_PRE_PING=true \
    AUTH_ENABLED=true \
    MICROSOFT_ENTRA_ID_TENANT_ID=secretref:microsoft-entra-id-tenant-id \
    MICROSOFT_ENTRA_ID_CLIENT_ID=secretref:microsoft-entra-id-client-id \
    MICROSOFT_ENTRA_ID_CLIENT_SECRET=secretref:microsoft-entra-id-client-secret \
    MICROSOFT_ENTRA_ID_REDIRECT_URI=secretref:microsoft-entra-id-redirect-uri \
    CORS_OVERRIDE_ALLOWED_ORIGINS="$CORS_OVERRIDE_ALLOWED_ORIGINS"
```

### 6.2. Allow the Container App identity to read secrets from the vault:

```bash
APP_PRINCIPAL_ID="$(az containerapp show -g "$RG" -n "$APP_NAME" --query identity.principalId -o tsv)"

az keyvault set-policy \
  -n "$KEYVAULT_NAME" \
  --object-id "$APP_PRINCIPAL_ID" \
  --secret-permissions get list
```

### 6.3. Configure app scaling:

```bash
az containerapp update -g "$RG" -n "$APP_NAME" --min-replicas 1 --max-replicas 1
```

> Note: the app may fail to start until Key Vault permissions propagate and the Key Vault-backed secrets are applied. If needed, re-deploy (or create a new revision) after the policy + secrets are in place.

## 7. Next steps

Once the app is running, continue with:

1. [Configure models](../../../admin/connect/models/overview.md)
2. [Configure knowledge providers](../../../admin/connect/knowledge-sources/overview.md)
3. [Configure API tools](../../../admin/connect/api-tools/configuration.md)