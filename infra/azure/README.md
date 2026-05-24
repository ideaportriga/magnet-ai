# Azure Infrastructure

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fideaportriga%2Fmagnet-ai%2Fmain%2Finfra%2Fazure%2Fazuredeploy.json)

The template is resource-group scoped — create (or select) a resource group first, then deploy into it.

## Authentication

**This template deploys the application with authentication disabled by default.** The Container App is publicly reachable on its `*.azurecontainerapps.io` URL until you enable Microsoft Entra ID auth.

Two things to do:

1. **On the initial deploy, set `ingressAllowedIpRange`** to your public IP (e.g. `1.2.3.4/32`) so the unauthenticated app is only reachable from that address. Without this the app is open to the internet.
2. **Follow [`azure_auth.md`](azure_auth.md)** to create an Entra ID app registration, wire up the `MICROSOFT_ENTRA_ID_*` values on the Container App, and flip `AUTH_ENABLED` to `true`. Entra app registration is a tenant-scoped Entra resource, not an Azure resource group resource, so it isn't created by this template — it must be set up separately.

Once auth is on, the IP restriction is optional (you can keep it as defense in depth, or remove it by redeploying with `ingressAllowedIpRange=""`).

## Required parameters

These two have no defaults and must be supplied on every deploy. **Pass the same values on every redeploy** — changing them will rotate the Postgres password (breaking existing connections) and invalidate the Fernet key (making previously-encrypted secrets in the database unreadable).

| Parameter | Type | Description |
|-----------|------|-------------|
| `postgresAdminPassword` | securestring | PostgreSQL admin password. 8+ chars, must contain uppercase, lowercase, digit, and special char (Azure Flexible Server complexity rules). |
| `secretEncryptionKey` | securestring | Fernet encryption key used by the app to encrypt stored credentials. Must be a 44-char url-safe base64 string ending in `=` (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`). |

## Optional parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `environment` | `dev` | Environment name (dev, staging, prod) — used in resource naming |
| `containerImageTag` | `latest` | Tag for the main magnet-ai image (`ghcr.io/ideaportriga/magnet-ai`) |
| `authEnabled` | `false` | Enable Entra ID auth on the magnet-ai app. Default is `false` so the first deploy succeeds without a pre-existing Entra app registration — flip to `true` and supply the three `entra*` params to turn auth on (see [`azure_auth.md`](azure_auth.md)). |
| `entraClientId` / `entraClientSecret` / `entraTenantId` | `''` | Entra ID app registration details (required when `authEnabled=true`) |
| `allowDevAccess` | `false` | Open Postgres and AI Foundry public access for a single dev IP (see below) |
| `devIpAddress` | `''` | IP to whitelist when `allowDevAccess=true` |
| `ingressAllowedIpRange` | `''` | CIDR range allowed through Container App ingress (empty = no restriction). Strongly recommended while `authEnabled=false`. |
| `loadDefaultData` | `false` | Load default providers/models/agents on first deploy. Set back to `false` after the initial seed. |
| `postgresServerName` | *(auto)* | Postgres server name. **Must be globally unique in Azure.** 3-63 chars, lowercase letters/digits/hyphens, start with a letter. Leave empty to auto-generate `psql-magnet-ai-<env>-<suffix>`. |
| `aiServicesAccountName` | *(auto)* | AI Services account name. **Must be globally unique in Azure.** 2-64 chars, alphanumeric + hyphens. Leave empty to auto-generate `ai-magnet-ai-<env>-<suffix>`. |

`<suffix>` is a deterministic 13-character string derived from the resource group ID (SHA-256-based, not random), so auto-generated names are stable across redeployments into the same RG and differ between RGs / subscriptions.

## Resources created

Networking:
- Virtual Network `vnet-magnet-ai-{env}` (10.0.0.0/16) with two subnets:
  - `container-apps` (10.0.0.0/23) — delegated to `Microsoft.App/environments`
  - `private-endpoints` (10.0.2.0/24)
- Private DNS zones (linked to the VNet): `privatelink.postgres.database.azure.com`, `privatelink.cognitiveservices.azure.com`, `privatelink.openai.azure.com`, `privatelink.services.ai.azure.com`
- Private endpoints for PostgreSQL and the AI Services account

Observability:
- Log Analytics Workspace `log-magnet-ai-{env}`

AI:
- Microsoft AI Services (Foundry) account `{aiServicesAccountName}` with default project `magnet-ai`, Defender-for-AI setting, and model deployments `gpt-4.1` and `gpt-4.1-mini` (GlobalStandard, capacity 250 each). Public network access disabled unless `allowDevAccess=true`.

Data:
- PostgreSQL Flexible Server `{postgresServerName}` (Burstable B2s, v17, 32 GB, 7-day backup) with database `magnet` and the `vector` extension enabled. Public access disabled unless `allowDevAccess=true`.

Compute:
- Container App Environment `cae-magnet-ai-{env}` (VNet-integrated via the `container-apps` subnet)
- Container App `ca-magnet-ai-{env}` — main magnet-ai backend (`ghcr.io/ideaportriga/magnet-ai`)

## CLI

### Deploy

```bash
az group create --name rg-magnet-ai-dev --location swedencentral

az deployment group create \
  --resource-group rg-magnet-ai-dev \
  --template-file infra/azure/main.bicep \
  --parameters \
    postgresAdminPassword="<strong-password>" \
    secretEncryptionKey="<fernet-key>" \
    ingressAllowedIpRange="$(curl -s ifconfig.me)/32"
```

Setting `ingressAllowedIpRange` on the initial deploy is the recommended default while auth is not yet enabled — it restricts the unauthenticated app to your current public IP.

To enable dev access to Postgres and the Foundry account from your workstation (temporarily opens their public endpoints to a single IP):

```bash
az deployment group create \
  --resource-group rg-magnet-ai-dev \
  --template-file infra/azure/main.bicep \
  --parameters \
    postgresAdminPassword="<strong-password>" \
    secretEncryptionKey="<fernet-key>" \
    allowDevAccess=true \
    devIpAddress="$(curl -s ifconfig.me)"
```

### Retrieve outputs

```bash
az deployment group show \
  --resource-group rg-magnet-ai-dev \
  --name main \
  --query properties.outputs
```

Outputs: `containerAppUrl`, `aiServicesEndpoint`, `aiServicesName`, `postgresServerFqdn`, `resourceGroupName`.

The template does **not** output AI Services keys. Fetch them post-deploy:

```bash
az cognitiveservices account keys list \
  --name <aiServicesName> \
  --resource-group rg-magnet-ai-dev
```

## Development

After modifying `.bicep` files, regenerate the ARM template:

```bash
az bicep build --file infra/azure/main.bicep --outfile infra/azure/azuredeploy.json
```

Commit the updated `azuredeploy.json` — it is the prebuilt ARM template used by the Deploy to Azure button.
