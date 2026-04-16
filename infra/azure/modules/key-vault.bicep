@description('Azure region for all resources')
param location string

@description('Key Vault name. Must be globally unique. 3-24 chars, alphanumeric + hyphens, must start with a letter.')
@minLength(3)
@maxLength(24)
param vaultName string

@description('Tenant ID that the vault authenticates against')
param tenantId string = subscription().tenantId

@description('Subnet resource ID for the private endpoint')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for privatelink.vaultcore.azure.net')
param privateDnsZoneId string

@description('Allow a single developer IP through the vault firewall for debugging (temporarily re-enables the public endpoint when true)')
param allowDevAccess bool = false

@description('Developer IP address to allow when allowDevAccess is true')
param devIpAddress string = ''

resource vault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: vaultName
  location: location
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: true
    // Private-only by default. AAD + RBAC + private endpoint gate access.
    // `allowDevAccess=true` opens a narrow public pinhole for the dev's IP.
    publicNetworkAccess: allowDevAccess ? 'Enabled' : 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
      ipRules: allowDevAccess && devIpAddress != '' ? [
        {
          value: devIpAddress
        }
      ] : []
    }
  }
}

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-kv-${vaultName}'
  location: location
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-kv-${vaultName}'
        properties: {
          privateLinkServiceId: vault.id
          groupIds: [
            'vault'
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
        name: 'keyvault'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

@description('Key Vault resource ID')
output vaultId string = vault.id

@description('Key Vault name')
output vaultName string = vault.name

@description('Key Vault URI (https://<name>.vault.azure.net/)')
output vaultUri string = vault.properties.vaultUri
