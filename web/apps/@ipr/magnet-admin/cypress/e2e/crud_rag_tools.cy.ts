/**
 * CRUD tests for RAG Tools via the UI.
 *
 * RAG Tools (Configuration) page has data-test selectors:
 *   search-input, new-btn, name-input, system_name-input, knowledge-sources
 */

describe('CRUD — RAG Tools', () => {
  const testPrefix = 'e2e-test-'

  beforeEach(() => {
    cy.viewport(1920, 1080)
  })

  it('opens the create dialog', () => {
    cy.visit('#/rag-tools')

    cy.g('new-btn').should('be.visible')
    cy.dismissErrors()

    cy.g('new-btn').click()
    cy.g('popup-confirm').should('be.visible')
    cy.g('name-input').should('exist')
  })

  it('searches for RAG tools', () => {
    cy.visit('#/rag-tools')

    cy.g('search-input').should('be.visible')
    cy.dismissErrors()

    cy.g('search-input').find('input').should('not.be.disabled').clear().type(testPrefix)
    cy.wait(500)

    // Table should update
    cy.get('.km-data-table', { timeout: 10000 }).should('exist')
  })
})
