/**
 * CRUD tests for Prompt Templates via the UI.
 *
 * Prompt Templates page has data-test selectors:
 *   search-input, new-btn, name-input, select-category
 * PopupConfirm buttons use data-test = the button label text (e.g. "Save")
 * Detail page: three-dot menu → Delete → km-popup-confirm
 */

describe('CRUD — Prompt Templates', () => {
  const testPrefix = 'e2e-test-'

  beforeEach(() => {
    cy.viewport(1920, 1080)
  })

  it('creates a new prompt template', () => {
    cy.visit('#/prompt-templates')

    // Wait for page to render, dismiss errors
    cy.g('new-btn').should('be.visible')
    cy.dismissErrors()

    cy.g('new-btn').click()
    cy.g('popup-confirm').should('be.visible')

    // Fill name (km-input wraps the actual <input>)
    cy.g('name-input').km_type()

    // Save (data-test="Save" on the confirm button)
    cy.g('Save').click()

    // After creation the app navigates to the detail page
    cy.url({ timeout: 15000 }).should('match', /prompt-templates\/[a-f0-9-]+/)
  })

  it('finds the created prompt template via search', () => {
    cy.visit('#/prompt-templates')
    cy.g('search-input').should('be.visible')
    cy.dismissErrors()

    // km-input wraps the actual <input> inside a <span data-test="search-input">
    cy.g('search-input').find('input').clear().type(testPrefix)
    cy.wait(500) // debounce

    cy.get('.km-data-table__row', { timeout: 10000 }).should('have.length.gte', 1)
  })

  it('opens a prompt template detail page from the list', () => {
    cy.visit('#/prompt-templates')
    cy.g('search-input').should('be.visible')
    cy.dismissErrors()

    cy.g('search-input').find('input').clear().type(testPrefix)
    cy.wait(500)

    cy.get('.km-data-table__row', { timeout: 10000 }).first().click()
    cy.url().should('match', /prompt-templates\/[a-f0-9-]+/)
  })

  it('deletes the created prompt template', () => {
    cy.visit('#/prompt-templates')
    cy.g('search-input').should('be.visible')
    cy.dismissErrors()

    cy.g('search-input').find('input').clear().type(testPrefix)
    cy.wait(500)

    cy.get('.km-data-table__row', { timeout: 10000 }).first().click()
    cy.url().should('match', /prompt-templates\/[a-f0-9-]+/)
    cy.dismissErrors()

    // Click three-dot menu
    cy.get('.fa-ellipsis-v', { timeout: 10000 }).closest('button').click()

    // Click "Delete" in dropdown
    cy.get('.q-menu .q-item').contains(/delete/i).click()

    // Confirm deletion
    cy.g('popup-confirm').should('be.visible')
    // The confirm button data-test is the translated "Delete Prompt Template" label
    // Use the last non-cancel button in the popup
    cy.g('popup-confirm').find('.q-card-actions button').last().click()

    // Should return to listing
    cy.url({ timeout: 10000 }).should('include', '/prompt-templates')
    cy.url().should('not.match', /prompt-templates\/[a-f0-9-]+/)
  })
})
