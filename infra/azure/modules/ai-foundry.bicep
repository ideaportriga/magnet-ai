@description('Azure region for all resources')
param location string

@description('Subnet resource ID for private endpoints')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for Cognitive Services (privatelink.cognitiveservices.azure.com)')
param cognitiveServicesDnsZoneId string

@description('Private DNS zone resource ID for OpenAI (privatelink.openai.azure.com)')
param openAiDnsZoneId string

@description('Private DNS zone resource ID for AI Services (privatelink.services.ai.azure.com)')
param aiServicesDnsZoneId string

@description('Allow public access for dev/debugging (adds devIpAddress to networkAcls)')
param allowDevAccess bool = false

@description('Developer IP address to allow when allowDevAccess is true')
param devIpAddress string = ''

@description('AI Services account name (globally unique). Override if default is taken.')
param aiServicesName string

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
      defaultAction: 'Deny'
      // Trusted Azure services path — needed so control-plane operations
      // (model deployment provisioning, MI token paths) reach the data plane
      // while the account is private-link-only. See:
      // https://learn.microsoft.com/azure/foundry/how-to/configure-private-link
      bypass: 'AzureServices'
      ipRules: allowDevAccess && devIpAddress != '' ? [
        {
          value: devIpAddress
        }
      ] : []
    }
    publicNetworkAccess: allowDevAccess ? 'Enabled' : 'Disabled'
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

// Private endpoint for VNet access
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-ai-${aiServicesName}'
  location: location
  dependsOn: [gpt41mini]
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-ai-${aiServicesName}'
        properties: {
          privateLinkServiceId: aiServices.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}

resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'cognitiveservices'
        properties: {
          privateDnsZoneId: cognitiveServicesDnsZoneId
        }
      }
      {
        name: 'openai'
        properties: {
          privateDnsZoneId: openAiDnsZoneId
        }
      }
      {
        name: 'aiservices'
        properties: {
          privateDnsZoneId: aiServicesDnsZoneId
        }
      }
    ]
  }
}

@description('AI Services endpoint URL')
output endpoint string = aiServices.properties.endpoint

@description('AI Services account name (use with: az cognitiveservices account keys list --name <name> --resource-group <rg>)')
output aiServicesName string = aiServices.name

@description('AI Services primary key')
output aiServicesKey string = aiServices.listKeys().key1
