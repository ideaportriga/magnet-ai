targetScope = 'subscription'

@description('Environment name (dev, staging, prod)')
param environment string = 'dev'

// Location is inherited from the deployment's location (--location in CLI, Region in portal)
var location = deployment().location

@description('Container image tag')
param containerImageTag string = 'latest'

@secure()
@description('PostgreSQL admin password')
param postgresAdminPassword string = 'ChangeMe123!'

@secure()
@description('Fernet encryption key for SECRET_ENCRYPTION_KEY')
param secretEncryptionKey string = 'ZmVybmV0LWRlZmF1bHQta2V5LWNoYW5nZW1l'

// ---------------------------------------------------------------------------
// Resource Group
// ---------------------------------------------------------------------------

var rgName = 'rg-magnet-ai-${environment}'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: rgName
  location: location
}

// ---------------------------------------------------------------------------
// Modules
// ---------------------------------------------------------------------------

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  scope: rg
  params: {
    environment: environment
    location: location
  }
}

module aiFoundry 'modules/ai-foundry.bicep' = {
  name: 'ai-foundry'
  scope: rg
  params: {
    environment: environment
    location: location
  }
}

module postgresql 'modules/postgresql.bicep' = {
  name: 'postgresql'
  scope: rg
  params: {
    environment: environment
    location: location
    adminPassword: postgresAdminPassword
  }
}

module containerAppEnv 'modules/container-app-env.bicep' = {
  name: 'container-app-env'
  scope: rg
  params: {
    environment: environment
    location: location
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
    logAnalyticsSharedKey: logAnalytics.outputs.sharedKey
  }
}

module containerApp 'modules/container-app.bicep' = {
  name: 'container-app'
  scope: rg
  params: {
    environment: environment
    location: location
    environmentId: containerAppEnv.outputs.environmentId
    envDefaultDomain: containerAppEnv.outputs.defaultDomain
    containerImage: 'ghcr.io/ideaportriga/magnet-ai:${containerImageTag}'
    databaseConnectionString: postgresql.outputs.connectionString
    secretEncryptionKey: secretEncryptionKey
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

@description('Full HTTPS URL of the backend container app')
output containerAppUrl string = containerApp.outputs.url

@description('AI Services endpoint URL')
output aiServicesEndpoint string = aiFoundry.outputs.endpoint

@description('AI Services account name')
output aiServicesName string = aiFoundry.outputs.aiServicesName

@description('AI Services API key')
#disable-next-line outputs-should-not-contain-secrets
output aiServicesApiKey string = aiFoundry.outputs.apiKey

@description('PostgreSQL server FQDN')
output postgresServerFqdn string = postgresql.outputs.serverFqdn

@description('Resource group name')
output resourceGroupName string = rgName
