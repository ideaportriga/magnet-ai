@description('Azure region for all resources')
param location string

@description('Environment name (used for naming the app UAMI)')
param environment string

@description('Key Vault name to grant Secrets User on')
param vaultName string

// ---------------------------------------------------------------------------
// User-assigned identity the Container App uses to resolve Key Vault secrets
// ---------------------------------------------------------------------------

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-magnet-ai-${environment}-app'
  location: location
}

resource vault 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: vaultName
}

// Key Vault Secrets User — read-only access to secret values
var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource appRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, appIdentity.id, kvSecretsUserRoleId)
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Resource ID of the app UAMI')
output appIdentityId string = appIdentity.id

@description('Principal ID of the app UAMI')
output appIdentityPrincipalId string = appIdentity.properties.principalId

@description('Client ID of the app UAMI')
output appIdentityClientId string = appIdentity.properties.clientId
