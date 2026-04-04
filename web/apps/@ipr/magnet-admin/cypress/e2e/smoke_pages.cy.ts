/**
 * Smoke tests — visit every page and verify no JS errors or crashes.
 *
 * Each test visits a route, waits for the page to settle, and relies on
 * the global error capture in e2e.ts to flag console.error / uncaught
 * exceptions.  If a page returns a backend 500 it will also be captured
 * via the backend-error task.
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
    it(`loads "${label}" (${route}) without errors`, () => {
      cy.viewport(1920, 1080)
      cy.visit(route)
      // Wait for the page to finish loading (network idle)
      cy.wait(1500)
      // Verify page rendered something (body is not empty)
      cy.get('body').should('not.be.empty')
      // Verify no error overlay / crash screen
      cy.get('body').should('not.contain.text', 'Internal Server Error')
      cy.get('body').should('not.contain.text', 'Application Error')
    })
  })
})
