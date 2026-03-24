@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for all resources')
param location string

var aiServicesName = 'mf-magnet-ai-${environment}'

resource aiServices 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiServicesName
  location: location
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: aiServicesName
    networkAcls: {
      defaultAction: 'Allow'
    }
    publicNetworkAccess: 'Enabled'
    allowProjectManagement: true
    defaultProject: 'magnet-ai'
    associatedProjects: [
      'magnet-ai'
    ]
  }
}

resource defenderSettings 'Microsoft.CognitiveServices/accounts/defenderForAISettings@2025-04-01-preview' = {
  parent: aiServices
  name: 'Default'
  properties: {
    state: 'Disabled'
  }
}

resource gpt41 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  dependsOn: [project]
  parent: aiServices
  name: 'gpt-4.1'
  sku: {
    name: 'GlobalStandard'
    capacity: 250
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1'
      version: '2025-04-14'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

resource gpt41mini 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  dependsOn: [gpt41]
  parent: aiServices
  name: 'gpt-4.1-mini'
  sku: {
    name: 'GlobalStandard'
    capacity: 250
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2025-04-14'
    }
    versionUpgradeOption: 'OnceNewDefaultVersionAvailable'
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  parent: aiServices
  name: 'magnet-ai'
  location: location
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    description: 'Default project created with the resource'
    displayName: 'magnet-ai'
  }
}

@description('AI Services endpoint URL')
output endpoint string = aiServices.properties.endpoint

@description('AI Services account name (use with az cognitiveservices account keys list)')
output aiServicesName string = aiServices.name

@description('AI Services API key')
#disable-next-line outputs-should-not-contain-secrets
output apiKey string = aiServices.listKeys().key1
