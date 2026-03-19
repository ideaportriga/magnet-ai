# Azure Marketplace Package

Resource-group-scoped ARM template + UI definition for Azure Marketplace (Solution Template).

## Files

- `mainTemplate.json` — ARM template deployed into the customer's resource group
- `createUiDefinition.json` — Portal wizard (collects environment + PostgreSQL password)

## Testing

### 1. Test the UI wizard only

Open the [CreateUiDefinition Sandbox](https://portal.azure.com/#blade/Microsoft_Azure_CreateUIDef/SandboxBlade), paste the contents of `createUiDefinition.json`, and click Preview. Verify the wizard renders correctly and outputs match `mainTemplate.json` parameters.

### 2. Test the ARM template only (CLI)

```bash
az group create --name rg-magnet-marketplace-test --location swedencentral

az deployment group create \
  --resource-group rg-magnet-marketplace-test \
  --template-file infra/azure/marketplace/mainTemplate.json \
  --parameters environment=dev postgresAdminPassword='YourP@ssw0rd!'
```

### 3. Test both together (Service Catalog)

This gives you the full Marketplace-like experience: UI wizard → deployment.

```bash
# Package
zip -j magnet-ai.zip mainTemplate.json createUiDefinition.json

# Upload to blob storage
az storage account create --name magnetmptest --resource-group rg-test --location swedencentral
az storage container create --name packages --account-name magnetmptest
az storage blob upload --account-name magnetmptest --container-name packages \
  --file magnet-ai.zip --name magnet-ai.zip
BLOB_URL=$(az storage blob url --account-name magnetmptest --container-name packages \
  --name magnet-ai.zip -o tsv)

# Create Service Catalog app definition
az managedapp definition create --name MagnetAI --location swedencentral \
  --resource-group rg-test --lock-level None \
  --display-name "Magnet AI" --description "Test deployment" \
  --package-file-uri "$BLOB_URL"

# Deploy from Azure Portal → Service Catalog → Managed Applications → MagnetAI
```

### 4. Validate with ARM TTK (optional)

```powershell
Install-Module -Name arm-ttk -Scope CurrentUser
Test-AzTemplate -TemplatePath infra/azure/marketplace/
```

## Packaging for Partner Center

```bash
zip -j magnet-ai-marketplace.zip mainTemplate.json createUiDefinition.json
```

Upload `magnet-ai-marketplace.zip` in Partner Center under your offer's technical configuration.
