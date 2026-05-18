export interface EntityAccessConfig {
  entityKey: string
  permissionResource: string
  readPermission: string
  writePermission: string
  deletePermission: string
  readonlyProvideKey: string
}

const entityAccess = {
  rag_tools: access('rag_tools', 'rag_tools', 'ragReadonly'),
  retrieval: access('retrieval', 'retrieval_tools', 'retrievalReadonly'),
} as const

function access(entityKey: string, permissionResource: string, readonlyProvideKey: string): EntityAccessConfig {
  return {
    entityKey,
    permissionResource,
    readPermission: `read:${permissionResource}`,
    writePermission: `write:${permissionResource}`,
    deletePermission: `delete:${permissionResource}`,
    readonlyProvideKey,
  }
}

export type EntityAccessKey = keyof typeof entityAccess

export function getEntityAccessConfig(entityKey: EntityAccessKey): EntityAccessConfig {
  return entityAccess[entityKey]
}

export { entityAccess }
