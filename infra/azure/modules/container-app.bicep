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

var appName = 'ca-magnet-ai-${environment}'
var redirectUri = 'https://${appName}.${envDefaultDomain}/auth/callback'

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      secrets: [
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
      ]
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
      }
    }
    template: {
      containers: [
        {
          image: containerImage
          name: appName
          env: [
            {
              name: 'AUTH_ENABLED'
              value: 'false'
            }
            {
              name: 'AUTH_ENABLED_FOR_SCHEMA'
              value: 'false'
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
