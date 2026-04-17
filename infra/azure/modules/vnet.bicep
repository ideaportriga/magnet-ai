@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for all resources')
param location string

var vnetName = 'vnet-magnet-ai-${environment}'

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: 'container-apps'
        properties: {
          addressPrefix: '10.0.0.0/23'
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: 'private-endpoints'
        properties: {
          addressPrefix: '10.0.2.0/24'
          // Explicit Disabled: ensures PE data-plane traffic isn't silently blocked
          // by subnet-level network policies, regardless of API default.
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

@description('VNet resource ID')
output vnetId string = vnet.id

@description('Container Apps subnet resource ID')
output containerAppsSubnetId string = vnet.properties.subnets[0].id

@description('Private Endpoints subnet resource ID')
output privateEndpointsSubnetId string = vnet.properties.subnets[1].id

