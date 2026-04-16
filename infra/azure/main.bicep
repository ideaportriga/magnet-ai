@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

// Location is inherited from the resource group
var location = resourceGroup().location

@description('Container image tag')
param containerImageTag string = 'latest'

@description('Enable authentication (Entra ID). Defaults to false so the template can deploy without a pre-existing Entra app registration; set to true and supply entraClientId/entraClientSecret/entraTenantId to turn auth on.')
param authEnabled bool = false

@description('Microsoft Entra ID Application (client) ID')
param entraClientId string = ''

@secure()
@description('Microsoft Entra ID client secret')
param entraClientSecret string = ''

@description('Microsoft Entra ID tenant ID')
param entraTenantId string = ''

@description('Allow public access to PostgreSQL, AI Services and Key Vault for dev/debugging')
param allowDevAccess bool = false

@description('Developer IP address to allow when allowDevAccess is true (e.g. 1.2.3.4)')
param devIpAddress string = ''

@description('IP range to restrict container app ingress (CIDR notation, e.g. 1.2.3.0/24). Empty = no restriction.')
param allowedIpRange string = ''

@description('PostgreSQL server name. Must be globally unique in Azure. 3-63 chars, lowercase letters/digits/hyphens, start with a letter. Leave empty to auto-generate: psql-magnet-ai-<env>-<suffix>.')
@maxLength(63)
param postgresServerName string = ''

@description('AI Services (Cognitive Services) account name. Must be globally unique in Azure. 2-64 chars, alphanumeric + hyphens. Leave empty to auto-generate: ai-magnet-ai-<env>-<suffix>.')
@maxLength(64)
param aiServicesAccountName string = ''

@description('Key Vault name. Must be globally unique in Azure. 3-24 chars, alphanumeric + hyphens, start with a letter. Leave empty to auto-generate: kv-<env>-<suffix>.')
@maxLength(24)
param keyVaultName string = ''

// ---------------------------------------------------------------------------
// Deterministic per-RG suffix for globally-unique resource names.
// uniqueString() is a SHA-256 hash of its inputs — same RG → same suffix on every
// redeploy, so names are stable. It is NOT random.
// ---------------------------------------------------------------------------

var uniqueSuffix = uniqueString(resourceGroup().id)
var resolvedPostgresServerName = empty(postgresServerName) ? 'psql-magnet-ai-${environment}-${uniqueSuffix}' : postgresServerName
var resolvedAiServicesName     = empty(aiServicesAccountName) ? 'ai-magnet-ai-${environment}-${uniqueSuffix}' : aiServicesAccountName
var resolvedKeyVaultName       = empty(keyVaultName) ? 'kv-${environment}-${uniqueSuffix}' : keyVaultName

// ---------------------------------------------------------------------------
// Modules
// ---------------------------------------------------------------------------

module vnet 'modules/vnet.bicep' = {
  name: 'vnet'

  params: {
    environment: environment
    location: location
  }
}

module privateDnsZones 'modules/private-dns-zones.bicep' = {
  name: 'private-dns-zones'

  params: {
    vnetId: vnet.outputs.vnetId
  }
}

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'

  params: {
    environment: environment
    location: location
  }
}

module keyVault 'modules/key-vault.bicep' = {
  name: 'key-vault'

  params: {
    location: location
    vaultName: resolvedKeyVaultName
    privateEndpointSubnetId: vnet.outputs.privateEndpointsSubnetId
    privateDnsZoneId: privateDnsZones.outputs.keyVaultDnsZoneId
    allowDevAccess: allowDevAccess
    devIpAddress: devIpAddress
  }
}

module secretsBootstrap 'modules/secrets-bootstrap.bicep' = {
  name: 'secrets-bootstrap'

  params: {
    location: location
    environment: environment
    vaultName: keyVault.outputs.vaultName
    scriptSubnetId: vnet.outputs.deploymentScriptsSubnetId
  }
}

module appIdentity 'modules/app-identity.bicep' = {
  name: 'app-identity'

  params: {
    location: location
    environment: environment
    vaultName: keyVault.outputs.vaultName
  }
}

module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'ai-foundry'

  params: {
    location: location
    aiServicesName: resolvedAiServicesName
    privateEndpointSubnetId: vnet.outputs.privateEndpointsSubnetId
    cognitiveServicesDnsZoneId: privateDnsZones.outputs.cognitiveServicesDnsZoneId
    openAiDnsZoneId: privateDnsZones.outputs.openAiDnsZoneId
    aiServicesDnsZoneId: privateDnsZones.outputs.aiServicesDnsZoneId
    allowDevAccess: allowDevAccess
    devIpAddress: devIpAddress
  }
}

// Read the freshly-bootstrapped postgres-admin-password out of KV via getSecret()
// so it stays @secure() end-to-end and never crosses a non-secure boundary.
resource kv 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: keyVault.outputs.vaultName
}

module postgresql 'modules/postgresql.bicep' = {
  name: 'postgresql'
  dependsOn: [
    secretsBootstrap
  ]

  params: {
    location: location
    serverName: resolvedPostgresServerName
    adminPassword: kv.getSecret('postgres-admin-password')
    privateEndpointSubnetId: vnet.outputs.privateEndpointsSubnetId
    privateDnsZoneId: privateDnsZones.outputs.postgresDnsZoneId
    allowDevAccess: allowDevAccess
    devIpAddress: devIpAddress
  }
}

module containerAppEnv 'modules/container-app-env.bicep' = {
  name: 'container-app-env'

  params: {
    environment: environment
    location: location
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsSharedKey: logAnalytics.outputs.sharedKey
    infrastructureSubnetId: vnet.outputs.containerAppsSubnetId
  }
}

module containerApp 'modules/container-app.bicep' = {
  name: 'container-app'
  dependsOn: [
    secretsBootstrap
  ]

  params: {
    environment: environment
    location: location
    environmentId: containerAppEnv.outputs.environmentId
    envDefaultDomain: containerAppEnv.outputs.defaultDomain
    containerImage: 'ghcr.io/ideaportriga/magnet-ai:${containerImageTag}'
    databaseConnectionString: postgresql.outputs.connectionString
    keyVaultUri: keyVault.outputs.vaultUri
    appIdentityId: appIdentity.outputs.appIdentityId
    authEnabled: authEnabled
    entraClientId: entraClientId
    entraClientSecret: entraClientSecret
    entraTenantId: entraTenantId
    allowedIpRange: allowedIpRange
  }
}

// ---------------------------------------------------------------------------
// Outputs (no secrets — use az CLI to fetch keys / KV secrets post-deploy)
// ---------------------------------------------------------------------------

@description('Full HTTPS URL of the backend container app')
output containerAppUrl string = containerApp.outputs.url

@description('AI Services endpoint URL')
output aiServicesEndpoint string = aiFoundry.outputs.endpoint

@description('AI Services account name (use: az cognitiveservices account keys list --name <name> --resource-group <rg>)')
output aiServicesName string = aiFoundry.outputs.aiServicesName

@description('PostgreSQL server FQDN')
output postgresServerFqdn string = postgresql.outputs.serverFqdn

@description('Key Vault name (holds postgres-admin-password and secret-encryption-key)')
output keyVaultName string = keyVault.outputs.vaultName

@description('Resource group name')
output resourceGroupName string = resourceGroup().name
