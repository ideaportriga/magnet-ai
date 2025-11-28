 
export interface SourceRow {
  id: string
  name: string
  type: string
  status?: string
  documents_count?: number
  created_at?: string
  last_sync_at?: string
  config?: Record<string, unknown>
}

export function getSourceTypeName(type: string) {
  switch (type) {
    case 'upload':
      return 'Manual Upload'
    case 'sharepoint':
      return 'SharePoint'
    case 'confluence':
      return 'Confluence'
    case 'salesforce':
      return 'Salesforce'
    case 'rightnow':
      return 'RightNow'
    case 'oracle_knowledge':
      return 'Oracle Knowledge'
    case 'hubspot':
      return 'HubSpot'
    case 'fluid_topics':
      return 'Fluid Topics'
    default:
      return type?.charAt(0).toUpperCase() + type?.slice(1)
  }
}

export function formatAdded(dateStr?: string) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`
  return date.toLocaleDateString()
}
