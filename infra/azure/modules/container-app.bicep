@description('Environment name (dev, staging, prod)')
param environment string

@description('Azure region for all resources')
param location string

@description('Container App Environment resource ID')
param environmentId string

@description('Default domain of the Container App Environment')
param envDefaultDomain string

@description('Container image to deploy')
param containerImage string

@secure()
@description('PostgreSQL connection string (asyncpg format)')
param databaseConnectionString string

@secure()
@description('Fernet encryption key')
param secretEncryptionKey string

@description('Enable authentication (Entra ID)')
param authEnabled bool = false

@description('Microsoft Entra ID Application (client) ID')
param entraClientId string = ''

@secure()
@description('Microsoft Entra ID client secret')
param entraClientSecret string = ''

@description('Microsoft Entra ID tenant ID')
param entraTenantId string = ''

@description('IP range to restrict ingress access (CIDR notation, e.g. 1.2.3.0/24). Empty = no restriction.')
param allowedIpRange string = ''

@description('Load default data into the database on startup')
param loadDefaultData bool = false

@description('Azure OpenAI endpoint URL for provider configuration')
param aiServicesEndpoint string = ''

@secure()
@description('Azure OpenAI API key for provider configuration')
param aiServicesKey string = ''

var appName = 'ca-magnet-ai-${environment}'
var redirectUri = 'https://${appName}.${envDefaultDomain}/auth/callback'

var baseSecrets = [
  {
    name: 'database-url'
    value: databaseConnectionString
  }
  {
    name: 'pgvector-connection-string'
    value: databaseConnectionString
  }
  {
    name: 'secret-encryption-key'
    value: secretEncryptionKey
  }
  {
    name: 'azure-openai-api-key'
    value: aiServicesKey
  }
]

var entraSecrets = authEnabled ? [
  {
    name: 'entra-client-id'
    value: entraClientId
  }
  {
    name: 'entra-client-secret'
    value: entraClientSecret
  }
] : []

var baseEnv = [
  {
    name: 'AUTH_ENABLED'
    value: authEnabled ? 'true' : 'false'
  }
  {
    name: 'AUTH_ENABLED_FOR_SCHEMA'
    value: authEnabled ? 'true' : 'false'
  }
  {
    name: 'ENV'
    value: environment
  }
  {
    name: 'DATABASE_URL'
    secretRef: 'database-url'
  }
  {
    name: 'PGVECTOR_CONNECTION_STRING'
    secretRef: 'pgvector-connection-string'
  }
  {
    name: 'SECRET_ENCRYPTION_KEY'
    secretRef: 'secret-encryption-key'
  }
  {
    name: 'MICROSOFT_ENTRA_ID_REDIRECT_URI'
    value: redirectUri
  }
  {
    name: 'RUN_MIGRATIONS'
    value: 'true'
  }
  {
    name: 'RUN_FIXTURES'
    value: loadDefaultData ? 'true' : 'false'
  }
  {
    name: 'AZURE_OPENAI_ENDPOINT'
    value: '${aiServicesEndpoint}openai/v1/'
  }
  {
    name: 'AZURE_OPENAI_API_KEY'
    secretRef: 'azure-openai-api-key'
  }
  {
    name: 'WEB_INCLUDED'
    value: 'true'
  }
  {
    name: 'HELP_BASE_URL'
    value: '/help'
  }
  {
    name: 'DATABASE_POOL_SIZE'
    value: '5'
  }
  {
    name: 'DATABASE_MAX_POOL_OVERFLOW'
    value: '3'
  }
  {
    name: 'DATABASE_POOL_TIMEOUT'
    value: '60'
  }
  {
    name: 'DATABASE_POOL_RECYCLE'
    value: '3600'
  }
  {
    name: 'DATABASE_PRE_POOL_PING'
    value: 'true'
  }
  {
    name: 'PGVECTOR_POOL_SIZE'
    value: '5'
  }
  {
    name: 'SCHEDULER_POOL_SIZE'
    value: '2'
  }
  {
    name: 'SCHEDULER_MAX_POOL_OVERFLOW'
    value: '0'
  }
  {
    name: 'SCHEDULER_POOL_TIMEOUT'
    value: '300'
  }
  {
    name: 'SCHEDULER_POOL_RECYCLE'
    value: '3600'
  }
  {
    name: 'SCHEDULER_POOL_PRE_PING'
    value: 'true'
  }
]

var entraEnv = authEnabled ? [
  {
    name: 'MICROSOFT_ENTRA_ID_CLIENT_ID'
    secretRef: 'entra-client-id'
  }
  {
    name: 'MICROSOFT_ENTRA_ID_CLIENT_SECRET'
    secretRef: 'entra-client-secret'
  }
  {
    name: 'MICROSOFT_ENTRA_ID_TENANT_ID'
    value: entraTenantId
  }
] : []

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      secrets: concat(baseSecrets, entraSecrets)
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'Auto'
        traffic: [
          {
            weight: 100
            latestRevision: true
          }
        ]
        allowInsecure: false
        ipSecurityRestrictions: allowedIpRange != '' ? [
          {
            name: 'AllowSpecificRange'
            action: 'Allow'
            ipAddressRange: allowedIpRange
          }
          {
            name: 'DenyAll'
            action: 'Deny'
            ipAddressRange: '0.0.0.0/0'
          }
        ] : []
      }
    }
    template: {
      containers: [
        {
          image: containerImage
          name: appName
          env: concat(baseEnv, entraEnv)
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            {
              type: 'Liveness'
              failureThreshold: 3
              periodSeconds: 10
              successThreshold: 1
              tcpSocket: {
                port: 8000
              }
              timeoutSeconds: 5
            }
            {
              type: 'Readiness'
              failureThreshold: 48
              periodSeconds: 5
              successThreshold: 1
              tcpSocket: {
                port: 8000
              }
              timeoutSeconds: 5
            }
            {
              type: 'Startup'
              failureThreshold: 240
              initialDelaySeconds: 1
              periodSeconds: 1
              successThreshold: 1
              tcpSocket: {
                port: 8000
              }
              timeoutSeconds: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

@description('Container App FQDN')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

@description('Full HTTPS URL of the container app')
output url string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
