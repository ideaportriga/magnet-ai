@description('Azure region for all resources')
param location string

@description('Environment name (used for naming the bootstrap UAMI)')
param environment string

@description('Key Vault name (scope for role assignment + target for secret writes)')
param vaultName string

@description('Subnet resource ID for the deployment script ACI (must be delegated to Microsoft.ContainerInstance/containerGroups). Required when the Key Vault is private-endpoint-only.')
param scriptSubnetId string

@description('Force re-run of the bootstrap script by changing this value. Default uses utcNow() only on new deployments.')
param forceUpdateTag string = utcNow()

// ---------------------------------------------------------------------------
// User-assigned identity the deployment script runs as
// ---------------------------------------------------------------------------

resource bootstrapIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-magnet-ai-${environment}-secrets-bootstrap'
  location: location
}

resource vault 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: vaultName
}

// Key Vault Secrets Officer — lets the script list/set/read secrets
var kvSecretsOfficerRoleId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'

resource bootstrapRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, bootstrapIdentity.id, kvSecretsOfficerRoleId)
  scope: vault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsOfficerRoleId)
    principalId: bootstrapIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---------------------------------------------------------------------------
// Deployment script — generate-if-missing for each secret
// ---------------------------------------------------------------------------

resource bootstrapScript 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'ds-magnet-ai-${environment}-secrets-bootstrap'
  location: location
  kind: 'AzureCLI'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${bootstrapIdentity.id}': {}
    }
  }
  dependsOn: [
    bootstrapRoleAssignment
  ]
  properties: {
    azCliVersion: '2.60.0'
    retentionInterval: 'PT1H'
    cleanupPreference: 'OnSuccess'
    timeout: 'PT15M'
    forceUpdateTag: forceUpdateTag
    // VNet integration so the ACI can reach a private-endpoint-only Key Vault.
    containerSettings: {
      subnetIds: [
        {
          id: scriptSubnetId
        }
      ]
    }
    environmentVariables: [
      {
        name: 'KV_NAME'
        value: vaultName
      }
    ]
    scriptContent: '''
set -eu

# Wait for RBAC propagation to the freshly created UAMI
for i in 1 2 3 4 5 6; do
  if az keyvault secret list --vault-name "$KV_NAME" --query "[].name" -o tsv >/dev/null 2>&1; then
    break
  fi
  echo "Waiting for RBAC propagation (attempt $i)..."
  sleep 10
done

secret_exists() {
  local name="$1"
  local found
  found=$(az keyvault secret list --vault-name "$KV_NAME" --query "[?name=='$name'].name" -o tsv 2>/dev/null || true)
  [ -n "$found" ]
}

# postgres-admin-password — Azure PG Flexible Server complexity:
# 8-128 chars, 3 of 4 {upper, lower, digit, non-alphanumeric}, not "postgres".
if secret_exists postgres-admin-password; then
  echo "postgres-admin-password already exists, skipping"
else
  RAND=$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 28)
  PWD="Pg1!${RAND}"
  az keyvault secret set --vault-name "$KV_NAME" --name postgres-admin-password --value "$PWD" --output none
  echo "Generated postgres-admin-password"
fi

# secret-encryption-key — Fernet key: 32 random bytes, url-safe-base64 encoded (44 chars, ends in =)
if secret_exists secret-encryption-key; then
  echo "secret-encryption-key already exists, skipping"
else
  FERNET=$(openssl rand 32 | base64 | tr '+/' '-_' | tr -d '\n=')
  FERNET="${FERNET}="
  az keyvault secret set --vault-name "$KV_NAME" --name secret-encryption-key --value "$FERNET" --output none
  echo "Generated secret-encryption-key"
fi

echo '{"bootstrapped": true}' > "$AZ_SCRIPTS_OUTPUT_PATH"
'''
  }
}

@description('Resource ID of the UAMI the bootstrap script runs as')
output bootstrapIdentityId string = bootstrapIdentity.id
