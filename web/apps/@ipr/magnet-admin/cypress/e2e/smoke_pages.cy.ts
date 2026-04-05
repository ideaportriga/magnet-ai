/**
 * Smoke tests — visit every page and verify it renders without crashing.
 *
 * Relies on the global error capture in e2e.ts to collect console.error
 * and uncaught exceptions into reports.
 */

const PAGES = [
  { route: '#/ai-apps', label: 'AI Apps' },
  { route: '#/prompt-templates', label: 'Prompt Templates' },
  { route: '#/knowledge-sources/', label: 'Knowledge Sources' },
  { route: '#/rag-tools', label: 'RAG Tools' },
  { route: '#/retrieval', label: 'Retrieval Tools' },
  { route: '#/deep-research/configs', label: 'Deep Research Configs' },
  { route: '#/deep-research/runs', label: 'Deep Research Runs' },
  { route: '#/model-providers', label: 'Model Providers' },
  { route: '#/model', label: 'Model Configuration' },
  { route: '#/agents', label: 'Agents' },
  { route: '#/observability-traces', label: 'Observability Traces' },
  { route: '#/evaluation-sets/', label: 'Evaluation Sets' },
  { route: '#/evaluation-jobs', label: 'Evaluation Jobs' },
  { route: '#/assistant-tools', label: 'Assistant Tools' },
  { route: '#/jobs', label: 'Jobs' },
  { route: '#/files', label: 'Files' },
  { route: '#/mcp', label: 'MCP Servers' },
  { route: '#/api-keys', label: 'API Keys' },
  { route: '#/api-servers', label: 'API Servers' },
  { route: '#/knowledge-providers', label: 'Knowledge Providers' },
  { route: '#/knowledge-graph', label: 'Knowledge Graph' },
  { route: '#/settings/import', label: 'Settings' },
  { route: '#/prompt-queue', label: 'Prompt Queue' },
  { route: '#/note-taker', label: 'Note Taker' },
  { route: '#/profile', label: 'Profile' },
  { route: '#/usage/rag', label: 'Usage' },
  { route: '#/conversation', label: 'Conversation' },
]

describe('Smoke — visit all pages', () => {
  PAGES.forEach(({ route, label }) => {
    it(`loads "${label}" (${route}) without crashing`, () => {
      cy.viewport(1920, 1080)
      cy.visit(route)

      // The page should render the app shell (sidebar, toolbar, or content area)
      cy.get('.q-layout, .q-page, #app', { timeout: 15000 }).should('exist')

      // Should NOT show a hard crash screen
      cy.get('body').should('not.contain.text', 'Application Error')
    })
  })
})
