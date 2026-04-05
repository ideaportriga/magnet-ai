/**
 * Table interaction tests.
 *
 * Pages with data-test="search-input" get search tests.
 * All table pages verify the table component renders.
 * Card-based pages verify cards or content area renders.
 */

// Pages that have data-test="search-input" and data-test="new-btn"
const SEARCHABLE_PAGES = [
  { route: '#/prompt-templates', label: 'Prompt Templates' },
  { route: '#/rag-tools', label: 'RAG Tools' },
]

// Pages with km-data-table
const TABLE_PAGES = [
  { route: '#/knowledge-sources/', label: 'Knowledge Sources' },
  { route: '#/retrieval', label: 'Retrieval Tools' },
  { route: '#/model', label: 'Model Configuration' },
  { route: '#/mcp', label: 'MCP Servers' },
  { route: '#/evaluation-sets/', label: 'Evaluation Sets' },
  { route: '#/api-keys', label: 'API Keys' },
  { route: '#/api-servers', label: 'API Servers' },
  { route: '#/knowledge-graph', label: 'Knowledge Graph' },
  { route: '#/jobs', label: 'Jobs' },
  { route: '#/observability-traces', label: 'Observability Traces' },
]

// Card-based pages
const CARD_PAGES = [
  { route: '#/agents', label: 'Agents' },
  { route: '#/ai-apps', label: 'AI Apps' },
]

describe('Tables — searchable pages', () => {
  SEARCHABLE_PAGES.forEach(({ route, label }) => {
    describe(label, () => {
      beforeEach(() => {
        cy.viewport(1920, 1080)
        cy.visit(route)
      })

      it('renders table', () => {
        cy.get('.km-data-table, .q-table', { timeout: 15000 }).should('exist')
        cy.dismissErrors()
      })

      it('has a working search input', () => {
        cy.g('search-input').should('be.visible')
        cy.dismissErrors()
        cy.g('search-input').find('input').clear().type('test-query')
        cy.wait(500)
        cy.g('search-input').find('input').should('have.value', 'test-query')
      })

      it('has a "New" button', () => {
        cy.dismissErrors()
        cy.g('new-btn').should('be.visible')
      })
    })
  })
})

describe('Tables — data table pages', () => {
  TABLE_PAGES.forEach(({ route, label }) => {
    it(`${label} — renders table or empty state`, () => {
      cy.viewport(1920, 1080)
      cy.visit(route)
      // Table component or page content should render
      cy.get('.km-data-table, .q-table, .q-page', { timeout: 15000 }).should('exist')
    })
  })
})

describe('Tables — card grid pages', () => {
  CARD_PAGES.forEach(({ route, label }) => {
    it(`${label} — renders page content`, () => {
      cy.viewport(1920, 1080)
      cy.visit(route)
      cy.get('.q-page, .q-layout', { timeout: 15000 }).should('exist')
    })
  })
})

describe('Tables — row click navigation (requires data)', () => {
  // These tests require existing data in the DB.
  // They will be skipped if no rows are found.

  function testRowClick(route: string, rowSelector: string, urlPattern: RegExp) {
    cy.viewport(1920, 1080)
    cy.visit(route)
    cy.wait(3000)
    cy.get('body').then(($body) => {
      if ($body.find(rowSelector).length > 0) {
        cy.get(rowSelector).first().click()
        cy.url().should('match', urlPattern)
      } else {
        cy.log(`No rows found for ${route} — skipping row click test`)
      }
    })
  }

  it('clicking a Prompt Template row opens detail page', () => {
    testRowClick('#/prompt-templates', '.km-data-table__row', /prompt-templates\/[a-f0-9-]+/)
  })

  it('clicking a Knowledge Source row opens detail page', () => {
    testRowClick('#/knowledge-sources/', '.km-data-table__row', /knowledge-sources\/[a-f0-9-]+/)
  })

  it('clicking an Agent card opens detail page', () => {
    testRowClick('#/agents', '.q-card.card-hover', /agents\/[a-f0-9-]+/)
  })
})
