/**
 * Human labels for permission `resource_type` values, kept in sync with the
 * sidebar menu tab names defined in `components/Toolbar.vue`.
 *
 * The permission matrix used to title-case the raw resource code, which
 * produced labels like "Ai Apps", "Api Keys", "Mcp Servers" or "Rag Tools"
 * that don't match the polished menu tabs ("AI Apps", "API Keys", "MCP Tools",
 * "RAG Tools"). To prevent the two from drifting, every resource that maps to a
 * menu tab reuses the *same* `nav_*` Paraglide message the menu renders.
 *
 * Resources without a dedicated menu tab fall back to a curated label with
 * correct acronym casing; anything unknown is title-cased as a last resort.
 */
import { m } from '@/paraglide/messages'

/** resource_type → menu tab label (reuses the menu's own i18n message). */
const NAV_LABEL: Record<string, () => string> = {
  agents: () => m.nav_agents(),
  ai_apps: () => m.nav_aiApps(),
  ai_models: () => m.nav_models(),
  api_keys: () => m.nav_apiKeys(),
  api_servers: () => m.nav_apiTools(),
  collections: () => m.nav_knowledgeSources(),
  deep_research: () => m.nav_deepResearch(),
  evaluations: () => m.nav_evaluations(),
  files: () => m.nav_fileStorage(),
  jobs: () => m.nav_jobs(),
  knowledge_graph: () => m.nav_knowledgeGraph(),
  mcp_servers: () => m.nav_mcpTools(),
  note_taker: () => m.nav_noteTaker(),
  observability: () => m.nav_observability(),
  prompt_queue: () => m.nav_promptQueue(),
  prompts: () => m.nav_promptTemplates(),
  rag_tools: () => m.nav_ragTools(),
  retrieval_tools: () => m.nav_retrievalTools(),
  traces: () => m.nav_traces(),
}

/** resource_type → curated label for resources with no dedicated menu tab. */
const STATIC_LABEL: Record<string, string> = {
  ai_edit: 'AI Edit',
  audit: 'Access Log',
  catalog: 'Catalog',
  groups: 'Groups',
  metrics: 'Metrics',
  oauth_clients: 'OAuth Clients',
  providers: 'Providers',
  resource_access: 'Resource Access',
  roles: 'Roles',
  scheduler: 'Scheduler',
  settings: 'Settings',
  users: 'Users',
}

/** Title-case a raw `snake_case` resource as a last-resort fallback. */
function titleCase(resource: string): string {
  return resource.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Display label for a permission `resource_type`, matching the menu tabs. */
export function resourceLabel(resourceType: string): string {
  const navLabel = NAV_LABEL[resourceType]
  if (navLabel) return navLabel()
  return STATIC_LABEL[resourceType] ?? titleCase(resourceType)
}
