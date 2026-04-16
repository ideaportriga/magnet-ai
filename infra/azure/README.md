# Azure Infrastructure

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fideaportriga%2Fmagnet-ai%2Fmain%2Finfra%2Fazure%2Fazuredeploy.json)

The template is resource-group scoped — create (or select) a resource group first, then deploy into it. **No user-supplied secrets are required:** the Postgres admin password and the Fernet encryption key are generated on the first deploy and stored in a Key Vault inside your resource group; every subsequent deploy reuses those same values.

## Parameters

All parameters are optional.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `environment` | `dev` | Environment name (dev, staging, prod) — used in resource naming |
| `containerImageTag` | `latest` | Tag for the main magnet-ai image (`ghcr.io/ideaportriga/magnet-ai`) |
| `authEnabled` | `false` | Enable Entra ID auth on the magnet-ai app. Default is `false` so the first deploy succeeds without a pre-existing Entra app registration — flip to `true` and supply the three `entra*` params to turn auth on. |
| `entraClientId` / `entraClientSecret` / `entraTenantId` | `''` | Entra ID app registration details (required when `authEnabled=true`) |
| `allowDevAccess` | `false` | Open Postgres, AI Foundry and Key Vault public access for a single dev IP (see below) |
| `devIpAddress` | `''` | IP to whitelist when `allowDevAccess=true` |
| `allowedIpRange` | `''` | CIDR range allowed through container-app ingress (empty = no restriction) |
| `postgresServerName` | *(auto)* | Postgres server name. **Must be globally unique in Azure.** 3-63 chars, lowercase letters/digits/hyphens, start with a letter. Leave empty to auto-generate `psql-magnet-ai-<env>-<suffix>`. |
| `aiServicesAccountName` | *(auto)* | AI Services account name. **Must be globally unique in Azure.** 2-64 chars, alphanumeric + hyphens. Leave empty to auto-generate `ai-magnet-ai-<env>-<suffix>`. |
| `keyVaultName` | *(auto)* | Key Vault name. **Must be globally unique in Azure.** 3-24 chars, alphanumeric + hyphens, start with a letter. Leave empty to auto-generate `kv-<env>-<suffix>`. |

`<suffix>` is a deterministic 13-character string derived from the resource group ID (SHA-256-based, not random), so auto-generated names are stable across redeployments into the same RG and differ between RGs / subscriptions.

## Secrets and Key Vault

On the **first** deployment, an ARM deployment script generates:

- `postgres-admin-password` — a strong random password that satisfies Azure PostgreSQL Flexible Server complexity rules
- `secret-encryption-key` — a 32-byte Fernet key (url-safe base64, 44 chars) used by the app to encrypt stored credentials

Both are written to the Key Vault. The Container App reads `secret-encryption-key` via a Key Vault reference using a user-assigned managed identity, and the Postgres admin password is passed securely via Bicep's `.getSecret()` at deploy time.

On every **subsequent** deployment, the script detects the existing secrets and leaves them untouched — so existing Fernet-encrypted data in the database remains decryptable.

To retrieve the generated values:

```bash
# Key Vault name is in the deployment outputs
az deployment group show -g rg-magnet-ai-dev -n main --query properties.outputs.keyVaultName.value -o tsv

# Read a secret
az keyvault secret show --vault-name <keyVaultName> --name postgres-admin-password --query value -o tsv
az keyvault secret show --vault-name <keyVaultName> --name secret-encryption-key     --query value -o tsv
```

**Tear-down note:** the Key Vault has soft-delete + purge-protection enabled, so it cannot be permanently deleted for 7 days after the resource group is removed. To reuse the same Key Vault name within that window you have to purge the soft-deleted vault first (`az keyvault purge --name <kvName>`) — or let the auto-generated suffix pick a new name.

## Resources created

Networking:
- Virtual Network `vnet-magnet-ai-{env}` (10.0.0.0/16) with three subnets:
  - `container-apps` (10.0.0.0/23) — delegated to `Microsoft.App/environments`
  - `private-endpoints` (10.0.2.0/24)
  - `deployment-scripts` (10.0.3.0/24) — delegated to `Microsoft.ContainerInstance/containerGroups` so the bootstrap deployment script can reach the private Key Vault
- Private DNS zones (linked to the VNet): `privatelink.postgres.database.azure.com`, `privatelink.cognitiveservices.azure.com`, `privatelink.openai.azure.com`, `privatelink.services.ai.azure.com`, `privatelink.vaultcore.azure.net`
- Private endpoints for PostgreSQL, the AI Services account, and the Key Vault

Observability:
- Log Analytics Workspace `log-magnet-ai-{env}`

AI:
- Microsoft AI Services (Foundry) account `{aiServicesAccountName}` with default project `magnet-ai`, Defender-for-AI setting, and model deployments `gpt-4.1` and `gpt-4.1-mini` (GlobalStandard, capacity 250 each). Public network access disabled unless `allowDevAccess=true`.

Data:
- PostgreSQL Flexible Server `{postgresServerName}` (Burstable B2s, v17, 32 GB, 7-day backup) with database `magnet` and the `vector` extension enabled. Public access disabled unless `allowDevAccess=true`.

Compute:
- Container App Environment `cae-magnet-ai-{env}` (VNet-integrated via the `container-apps` subnet)
- Container App `ca-magnet-ai-{env}` — main magnet-ai backend (`ghcr.io/ideaportriga/magnet-ai`), with a user-assigned managed identity (`id-magnet-ai-{env}-app`) that has `Key Vault Secrets User` on the vault.

Secrets:
- Key Vault `{keyVaultName}` (RBAC, soft-delete + purge-protection enabled, **private-endpoint only** — public access disabled unless `allowDevAccess=true`)
- User-assigned managed identity `id-magnet-ai-{env}-secrets-bootstrap` with `Key Vault Secrets Officer` on the vault
- Deployment script `ds-magnet-ai-{env}-secrets-bootstrap` (VNet-integrated via the `deployment-scripts` subnet) that generates `postgres-admin-password` and `secret-encryption-key` on first deploy, and is a no-op on subsequent deploys

## CLI

### Deploy

```bash
az group create --name rg-magnet-ai-dev --location swedencentral

az deployment group create \
  --resource-group rg-magnet-ai-dev \
  --template-file infra/azure/main.bicep
```

To restrict Container App ingress to your current public IP at deploy time:

```bash
az deployment group create \
  --resource-group rg-magnet-ai-dev \
  --template-file infra/azure/main.bicep \
  --parameters allowedIpRange="$(curl -s ifconfig.me)/32"
```

To enable dev access to Postgres, the Foundry account and the Key Vault from your workstation (temporarily opens their public endpoints to a single IP):

```bash
az deployment group create \
  --resource-group rg-magnet-ai-dev \
  --template-file infra/azure/main.bicep \
  --parameters allowDevAccess=true devIpAddress="$(curl -s ifconfig.me)"
```

### Retrieve outputs

```bash
az deployment group show \
  --resource-group rg-magnet-ai-dev \
  --name main \
  --query properties.outputs
```

Outputs: `containerAppUrl`, `aiServicesEndpoint`, `aiServicesName`, `postgresServerFqdn`, `keyVaultName`, `resourceGroupName`.

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
