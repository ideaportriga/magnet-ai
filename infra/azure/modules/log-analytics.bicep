@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for all resources')
param location string

var workspaceName = 'log-magnet-ai-${environment}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

@description('Resource ID of the Log Analytics workspace')
output workspaceId string = logAnalytics.id

@description('Customer ID (workspace ID) for log analytics configuration')
output customerId string = logAnalytics.properties.customerId

@description('Primary shared key for log analytics')
#disable-next-line outputs-should-not-contain-secrets
output sharedKey string = logAnalytics.listKeys().primarySharedKey
