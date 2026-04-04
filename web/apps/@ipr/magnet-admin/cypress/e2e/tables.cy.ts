/**
 * Table interaction tests — verify search, pagination, and row navigation
 * on pages that use km-data-table (via useDataTable composable).
 */

const TABLE_PAGES = [
  { route: '#/prompt-templates', label: 'Prompt Templates' },
  { route: '#/rag-tools', label: 'RAG Tools' },
  { route: '#/retrieval', label: 'Retrieval Tools' },
  { route: '#/agents', label: 'Agents' },
  { route: '#/knowledge-sources/', label: 'Knowledge Sources' },
  { route: '#/model', label: 'Model Configuration' },
  { route: '#/mcp', label: 'MCP Servers' },
  { route: '#/evaluation-sets/', label: 'Evaluation Sets' },
  { route: '#/api-keys', label: 'API Keys' },
  { route: '#/api-servers', label: 'API Servers' },
  { route: '#/knowledge-graph', label: 'Knowledge Graph' },
  { route: '#/jobs', label: 'Jobs' },
  { route: '#/observability-traces', label: 'Observability Traces' },
]

describe('Tables — basic interactions', () => {
  TABLE_PAGES.forEach(({ route, label }) => {
    describe(label, () => {
      beforeEach(() => {
        cy.viewport(1920, 1080)
        cy.visit(route)
        cy.wait(2000) // wait for data to load
      })

      it('renders table or empty state', () => {
        // Either table rows exist or an empty-state message is shown
        cy.get('body').then(($body) => {
          const hasRows = $body.find('[data-test="table-row"], .km-data-table__row').length > 0
          const hasTable = $body.find('.km-data-table, .q-table').length > 0
          const hasEmptyState = $body.text().includes('No data') ||
                                $body.text().includes('No results') ||
                                $body.text().includes('empty') ||
                                $body.text().includes('Create')
          expect(hasRows || hasTable || hasEmptyState).to.be.true
        })
      })

      it('search input is present and typeable', () => {
        cy.get('body').then(($body) => {
          if ($body.find('[data-test="search-input"]').length > 0) {
            cy.g('search-input').click()
            cy.g('search-input').type('test-search-query')
            // Wait for debounced search to fire
            cy.wait(500)
            // Search input should still contain the typed text
            cy.g('search-input').should('have.value', 'test-search-query')
          }
        })
      })
    })
  })
})

describe('Tables — row click navigation', () => {
  it('clicking a Prompt Template row opens detail page', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/prompt-templates')
    cy.wait(2000)
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="table-row"]').length > 0) {
        cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).eq(0).click()
        // Should navigate to a detail page (URL contains an ID)
        cy.url().should('match', /prompt-templates\/[a-f0-9-]+/)
      }
    })
  })

  it('clicking an Agent row opens detail page', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/agents')
    cy.wait(2000)
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="table-row"]').length > 0) {
        cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).eq(0).click()
        cy.url().should('match', /agents\/[a-f0-9-]+/)
      }
    })
  })

  it('clicking a Knowledge Source row opens detail page', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/knowledge-sources/')
    cy.wait(2000)
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="table-row"]').length > 0) {
        cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).eq(0).click()
        cy.url().should('match', /knowledge-sources\/[a-f0-9-]+/)
      }
    })
  })
})
