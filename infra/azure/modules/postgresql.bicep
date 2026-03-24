@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for all resources')
param location string

@secure()
@description('Administrator password for PostgreSQL')
param adminPassword string

var serverName = 'psql-magnet-ai-${environment}'
var databaseName = 'magnet'

resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: serverName
  location: location
  sku: {
    name: 'Standard_B2s'
    tier: 'Burstable'
  }
  properties: {
    version: '17'
    administratorLogin: 'postgres'
    administratorLoginPassword: adminPassword
    storage: {
      storageSizeGB: 32
      autoGrow: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
    authConfig: {
      activeDirectoryAuth: 'Disabled'
      passwordAuth: 'Enabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    dataEncryption: {
      type: 'SystemManaged'
    }
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgresServer
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource allowAzureServices 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = {
  parent: postgresServer
  name: 'AllowAllAzureServicesAndResourcesWithinAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource vectorExtension 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  parent: postgresServer
  name: 'azure.extensions'
  properties: {
    value: 'VECTOR'
    source: 'user-override'
  }
  dependsOn: [database]
}

@description('PostgreSQL server FQDN')
output serverFqdn string = postgresServer.properties.fullyQualifiedDomainName

@description('Connection string for the magnet database (asyncpg format)')
#disable-next-line outputs-should-not-contain-secrets
output connectionString string = 'postgresql+asyncpg://postgres:${adminPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/${databaseName}'
