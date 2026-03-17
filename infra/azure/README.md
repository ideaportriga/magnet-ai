# Azure Infrastructure

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fideaportriga%2Fmagnet-ai%2Fmain%2Finfra%2Fazure%2Fazuredeploy.json)

Click the button above and fill in the parameters in Azure Portal:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Region | `swedencentral` | Azure region for all resources |
| Environment | `dev` | Environment name (dev, staging, prod) |
| Container Image Tag | `latest` | Container image tag |
| Postgres Admin Password | `ChangeMe123!` | PostgreSQL admin password |
| Secret Encryption Key | *(default provided)* | Fernet encryption key |

## Resources created

- Resource Group (`rg-magnet-ai-{env}`)
- Log Analytics Workspace (`log-magnet-ai-{env}`)
- Microsoft Foundry + GPT-4.1 and GPT-4.1-mini models (`mf-magnet-ai-{env}`)
- PostgreSQL Flexible Server + `magnet` database (`psql-magnet-ai-{env}`)
- Container App Environment (`cae-magnet-ai-{env}`)
- Container App (`ca-magnet-ai-{env}`)

## CLI

### Deploy

```bash
az deployment sub create --location swedencentral --template-file infra/main.bicep
```

With parameters:

```bash
az deployment sub create --location swedencentral --template-file infra/main.bicep \
  --parameters environment=staging postgresAdminPassword='YourPassword'
```

### Retrieve outputs

```bash
az deployment sub show --name <deployment-name> --query properties.outputs
```

Returns: container app URL, AI endpoint, AI API key, PostgreSQL FQDN.

## Development

After modifying `.bicep` files, regenerate the ARM template:

```bash
az bicep build --file main.bicep --outfile azuredeploy.json
```

Commit the updated `azuredeploy.json` — it is the prebuilt ARM template used by the Deploy to Azure button.
