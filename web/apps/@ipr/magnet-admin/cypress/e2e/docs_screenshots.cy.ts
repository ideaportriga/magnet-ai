/**
 * Documentation screenshot capture (ai-claude).
 *
 * Visits every admin page and snaps a full-page screenshot named after the
 * route. Output is written to `<repo>/reports/screenshots/docs_screenshots*`
 * by the Cypress config. Copy/symlink the desired files into
 * `web/documentation/magnet/docs/en/images/` to embed them in docs.
 *
 * Run with the dev server + backend already up:
 *     npx nx e2e magnet-admin --testPathPattern=docs_screenshots
 */

const PAGES: { route: string; name: string }[] = [
  // Authentication & profile
  { route: '#/profile', name: 'profile' },

  // RBAC (new in alpha)
  { route: '#/admin/users', name: 'admin-users-list' },
  { route: '#/admin/roles', name: 'admin-roles-list' },
  { route: '#/admin/access-log', name: 'admin-access-log' },

  // Core configuration
  { route: '#/agents', name: 'agents-list' },
  { route: '#/prompt-templates', name: 'prompt-templates-list' },
  { route: '#/rag-tools', name: 'rag-tools-list' },
  { route: '#/retrieval', name: 'retrieval-tools-list' },
  { route: '#/knowledge-sources/', name: 'knowledge-sources-list' },
  { route: '#/knowledge-graph', name: 'knowledge-graph' },
  { route: '#/ai-apps', name: 'ai-apps-list' },

  // Models & integrations
  { route: '#/model-providers', name: 'model-providers' },
  { route: '#/model', name: 'model-configuration' },
  { route: '#/api-servers', name: 'api-servers' },
  { route: '#/mcp', name: 'mcp-servers' },

  // Observability
  { route: '#/observability-traces', name: 'observability-traces' },
  { route: '#/usage/rag', name: 'usage-rag' },

  // Other features
  { route: '#/deep-research/configs', name: 'deep-research-configs' },
  { route: '#/deep-research/runs', name: 'deep-research-runs' },
  { route: '#/evaluation-sets/', name: 'evaluation-sets' },
  { route: '#/evaluation-jobs', name: 'evaluation-jobs' },
  { route: '#/assistant-tools', name: 'assistant-tools' },
  { route: '#/note-taker', name: 'note-taker' },
  { route: '#/prompt-queue', name: 'prompt-queue' },
  { route: '#/jobs', name: 'jobs' },
  { route: '#/files', name: 'files' },
  { route: '#/api-keys', name: 'api-keys' },
  { route: '#/settings/import', name: 'settings-import-export' },
]

describe('Documentation screenshots', () => {
  PAGES.forEach(({ route, name }) => {
    it(`captures ${name} (${route})`, () => {
      cy.viewport(1600, 1000)
      cy.visit(route)
      // Wait for the app shell so we never screenshot a blank canvas.
      cy.get('.km-layout, [data-test="header"], .km-page-container, #app', {
        timeout: 20000,
      }).should('exist')
      // Give async query loaders a beat to populate tables.
      cy.wait(800)
      cy.screenshot(`docs/${name}`, {
        capture: 'viewport',
        overwrite: true,
      })
    })
  })
})
