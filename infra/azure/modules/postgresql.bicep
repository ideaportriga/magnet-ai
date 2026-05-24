@description('Azure region for all resources')
param location string

@secure()
@description('Administrator password for PostgreSQL')
param adminPassword string

@description('Subnet resource ID for private endpoints')
param privateEndpointSubnetId string

@description('Private DNS zone resource ID for PostgreSQL')
param privateDnsZoneId string

@description('Allow public access for dev/debugging (adds devIpAddress to firewall)')
param allowDevAccess bool = false

@description('Developer IP address to allow when allowDevAccess is true')
param devIpAddress string = ''

@description('PostgreSQL server name (globally unique). Override if default is taken.')
param serverName string

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
      publicNetworkAccess: allowDevAccess ? 'Enabled' : 'Disabled'
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

resource vectorExtension 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2024-08-01' = {
  parent: postgresServer
  name: 'azure.extensions'
  properties: {
    value: 'VECTOR'
    source: 'user-override'
  }
  dependsOn: [database]
}

// Dev access: allow a specific IP when debugging
resource devFirewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = if (allowDevAccess && devIpAddress != '') {
  parent: postgresServer
  name: 'AllowDevAccess'
  properties: {
    startIpAddress: devIpAddress
    endIpAddress: devIpAddress
  }
}

// Private endpoint for VNet access
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: 'pe-pg-${serverName}'
  location: location
  dependsOn: [vectorExtension]
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'pe-pg-${serverName}'
        properties: {
          privateLinkServiceId: postgresServer.id
          groupIds: [
            'postgresqlServer'
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
        name: 'postgres'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

@description('PostgreSQL server FQDN')
output serverFqdn string = postgresServer.properties.fullyQualifiedDomainName

@description('Connection string for the magnet database (asyncpg format)')
#disable-next-line outputs-should-not-contain-secrets
output connectionString string = 'postgresql+asyncpg://postgres:${adminPassword}@${postgresServer.properties.fullyQualifiedDomainName}:5432/${databaseName}'
