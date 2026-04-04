/**
 * CRUD tests for Agents via the UI.
 * Create → verify in list → open → delete.
 */

describe('CRUD — Agents', () => {
  const testPrefix = 'e2e-test-'

  it('creates a new agent', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/agents')
    cy.wait(3000)
    cy.dismissErrors()
    cy.g('new-btn').click()

    // Fill name
    cy.g('name-input').click()
    cy.g('name-input').km_type()

    // Save
    cy.g('Save').click()
    cy.wait(1500)
  })

  it('finds the created agent in the list', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/agents')
    cy.wait(3000)
    cy.dismissErrors()
    cy.g('search-input').click()
    cy.g('search-input').type(testPrefix)
    cy.wait(1000)
    cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).should('have.length.gte', 1)
  })

  it('opens agent detail page', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/agents')
    cy.wait(3000)
    cy.dismissErrors()
    cy.g('search-input').click()
    cy.g('search-input').type(testPrefix)
    cy.wait(1000)
    cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).eq(0).click()
    cy.url().should('match', /agents\/[a-f0-9-]+/)
  })

  it('deletes the created agent', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/agents')
    cy.wait(3000)
    cy.dismissErrors()
    cy.g('search-input').click()
    cy.g('search-input').type(testPrefix)
    cy.wait(1000)
    cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).eq(0).click()
    cy.g('show-more-btn').click()
    cy.g('delete-btn').click()
    cy.g('popup-confirm').should('be.visible')
    cy.g('popup-confirm').find('button').last().click()
    cy.wait(1000)
  })
})
