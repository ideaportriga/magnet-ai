@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for all resources')
param location string

@description('Log Analytics workspace customer ID')
param logAnalyticsCustomerId string

@secure()
@description('Log Analytics workspace shared key')
param logAnalyticsSharedKey string

var envName = 'cae-magnet-ai-${environment}'

resource containerAppEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    zoneRedundant: false
    peerAuthentication: {
      mtls: {
        enabled: false
      }
    }
  }
}

@description('Container App Environment resource ID')
output environmentId string = containerAppEnv.id

@description('Default domain of the Container App Environment')
output defaultDomain string = containerAppEnv.properties.defaultDomain
