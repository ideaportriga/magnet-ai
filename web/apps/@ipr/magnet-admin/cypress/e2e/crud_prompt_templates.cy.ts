/**
 * CRUD tests for Prompt Templates via the UI.
 * Create → verify in list → open → update → delete.
 */

describe('CRUD — Prompt Templates', () => {
  const testPrefix = 'e2e-test-'

  it('creates a new prompt template', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/prompt-templates')
    cy.wait(3000)
    cy.dismissErrors()
    cy.get('[data-test="new-btn"]', { timeout: 15000 }).should('be.visible').click()

    // Verify validation: save without name shows error
    cy.g('Save').click()
    cy.g('popup-confirm').contains('Field can not be empty')

    // Fill in the name
    cy.g('name-input').click()
    cy.g('name-input').km_type()

    // Select category
    cy.km_select('select-category', 'RAG')

    // Save
    cy.g('Save').click()

    // Should navigate to detail page or stay on list with new item
    cy.wait(1000)
  })

  it('finds the created prompt template in the list', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/prompt-templates')
    cy.wait(3000)
    cy.dismissErrors()
    cy.g('search-input').click()
    cy.g('search-input').type(testPrefix)
    cy.wait(1000) // debounce
    // At least one row should match
    cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).should('have.length.gte', 1)
  })

  it('opens a prompt template detail page', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/prompt-templates')
    cy.wait(3000)
    cy.dismissErrors()
    cy.g('search-input').click()
    cy.g('search-input').type(testPrefix)
    cy.wait(1000)
    cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).eq(0).click()
    // Should be on a detail page
    cy.url().should('match', /prompt-templates\/[a-f0-9-]+/)
  })

  it('deletes the created prompt template', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/prompt-templates')
    cy.wait(3000)
    cy.dismissErrors()
    cy.g('search-input').click()
    cy.g('search-input').type(testPrefix)
    cy.wait(1000)
    cy.get('[data-test="table-row"], .km-data-table__row', { timeout: 10000 }).eq(0).click()

    // Open more menu and delete
    cy.g('show-more-btn').click()
    cy.g('delete-btn').click()

    // Confirm deletion
    cy.g('popup-confirm').contains('You are about to delete the Prompt Template')
    cy.g('Delete Prompt Template').click()
    cy.wait(1000)
  })
})
