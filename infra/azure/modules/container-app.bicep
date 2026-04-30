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

@secure()
@description('SECRET_KEY for JWT auth. Generate with `openssl rand -hex 32`.')
param secretKey string = ''

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
        {
          name: 'secret-key'
          value: secretKey
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
      // Must be ≥ TASKIQ_DEFAULT_TIMEOUT_SECONDS so SIGTERM lets a
      // long-running task (sync_kg_source / api_ingest can each be 30 min)
      // finish before the replica is force-killed. The
      // TaskiqRuntimePlugin._stop_runtime caps wait at
      // TASKIQ_WAIT_TASKS_TIMEOUT (1860s).
      terminationGracePeriodSeconds: 1900
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
              name: 'SECRET_KEY'
              secretRef: 'secret-key'
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
            // ---- TaskIQ (single-container in-process layout) ----
            // Worker and scheduler run as asyncio tasks inside the
            // Litestar event loop via TaskiqRuntimePlugin. Concurrency is
            // kept low because heavy CPU work in the worker would block
            // API request handling on the same loop.
            {
              name: 'TASKIQ_INPROCESS_WORKER_ENABLED'
              value: 'true'
            }
            {
              name: 'TASKIQ_INPROCESS_SCHEDULER_ENABLED'
              value: 'true'
            }
            {
              name: 'TASKIQ_WORKER_CONCURRENCY'
              value: '2'
            }
            {
              name: 'TASKIQ_DEFAULT_TIMEOUT_SECONDS'
              value: '1800'
            }
            {
              name: 'TASKIQ_WAIT_TASKS_TIMEOUT'
              value: '1860'
            }
            {
              name: 'TASKIQ_SCHEDULER_UPDATE_INTERVAL'
              value: '10'
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          probes: [
            // Liveness: hit /health/live which inspects the in-process
            // TaskIQ worker / scheduler asyncio tasks. A dead runtime
            // task is not recoverable inside the same process — let
            // Container Apps recycle the replica.
            {
              type: 'Liveness'
              failureThreshold: 3
              periodSeconds: 10
              successThreshold: 1
              httpGet: {
                path: '/health/live'
                port: 8000
                scheme: 'HTTP'
              }
              timeoutSeconds: 5
            }
            // Readiness: deeper probe (DB pool, API key cache, taskiq
            // tasks). 503 here only takes the replica out of ingress
            // rotation, not restarts it.
            {
              type: 'Readiness'
              failureThreshold: 48
              periodSeconds: 5
              successThreshold: 1
              httpGet: {
                path: '/health/ready'
                port: 8000
                scheme: 'HTTP'
              }
              timeoutSeconds: 5
            }
            // Startup: keep TCP — /health endpoints aren't bound until
            // Litestar finishes its plugin chain.
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
        // SINGLETON. The in-process scheduler MUST be the only scheduler
        // running against `taskiq_schedules` — multiple replicas would
        // double-fire every cron tick. To horizontally scale API in the
        // future, move scheduler into its own Container App and keep
        // THAT one at maxReplicas: 1.
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
