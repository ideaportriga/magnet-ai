export type SourceScheduleCron = {
  year?: number | string | null
  month?: number | string | null
  day?: number | string | null
  week?: number | string | null
  day_of_week?: number | string | null
  hour?: number | string | null
  minute?: number | string | null
  second?: number | string | null
  start_date?: string | null
  end_date?: string | null
  jitter?: number | null
}

export type SourceSchedule = {
  name?: string | null
  interval?: string | null
  cron?: SourceScheduleCron | null
  timezone?: string | null
} | null

export type SourcePhaseStats = {
  completed: number
  failed: number
  running: number
  total: number
}

export type SourceStats = {
  documents_count: number
  sync: SourcePhaseStats
  metadata: SourcePhaseStats
  entities: SourcePhaseStats
}

export type SourceLastSyncError = {
  document: string
  message?: string | null
}

export type SourceLastSync = {
  started_at?: string | null
  completed_at?: string | null
  duration_seconds?: number | null
  outcome?: string | null
  total_found: number
  synced: number
  failed: number
  skipped: number
  unchanged_skipped: number
  metadata_only_updated: number
  content_changed: number
  deleted: number
  errors: SourceLastSyncError[]
}

export type SourceSyncProgress = {
  phase?: string | null
  processed: number
  total: number
  current_document?: string | null
  started_at?: string | null
  updated_at?: string | null
}

export interface SourceRow {
  id: string
  name: string
  type: string
  status?: string
  documents_count?: number
  created_at?: string
  last_sync_at?: string
  config?: Record<string, unknown>
  schedule?: SourceSchedule
  stats?: SourceStats | null
  last_sync?: SourceLastSync | null
  sync_progress?: SourceSyncProgress | null
}

export function getSourceTypeName(type: string) {
  switch (type) {
    case 'upload':
      return 'Manual Upload'
    case 'api_ingest':
      return 'API Ingest'
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
      return type
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
