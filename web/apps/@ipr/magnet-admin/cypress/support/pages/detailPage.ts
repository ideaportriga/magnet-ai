/// <reference types="cypress" />

/**
 * Page-object helpers for entity detail pages (`/<entity>/:id`).
 *
 * Relies on data-test attributes added in the I.2 audit:
 *   - `name-input`, `description-input`, `system-name-input` — header fields
 *   - `save-btn` — save changes (disabled when !isDirty)
 *   - `revert-btn` — revert local draft (visible only when isDirty)
 *   - `show-more-btn` — three-dot menu trigger
 *   - `delete-btn` — menu item inside the three-dot menu
 *
 * Delete confirmation uses `km-popup-confirm` — see createDialog.save/cancel
 * for the `data-test-role` pattern.
 */

export const detailPage = {
  /** Wait until the detail page has finished loading (header input is visible). */
  waitForLoad() {
    cy.g('name-input', { timeout: 15000 }).should('be.visible')
  },

  /** Assert the URL matches `/<entity>/<uuid>` (or similar). */
  expectOnDetailPage(entityPathSegment: string) {
    const rx = new RegExp(`${entityPathSegment}/[a-f0-9-]{8,}`)
    cy.url({ timeout: 15000 }).should('match', rx)
  },

  /** Return the current value of the name input. Chainable for assertions. */
  readName() {
    return cy.g('name-input').find('input').invoke('val')
  },

  /** Type into the name field (overwriting current value). */
  setName(value: string) {
    cy.g('name-input').find('input').clear().type(value).blur()
  },

  /** Type into the description field. */
  setDescription(value: string) {
    cy.g('description-input').find('input, textarea').first().clear().type(value).blur()
  },

  /** Click the Save button in the header. Waits for it to be enabled. */
  save() {
    cy.g('save-btn', { timeout: 10000 }).should('not.be.disabled').click()
  },

  /** Click the Revert button (visible only when there are unsaved changes). */
  revert() {
    cy.g('revert-btn').click()
  },

  /** Open the three-dot menu and click Delete → confirm in the popup. */
  deleteEntity() {
    cy.g('show-more-btn').click()
    cy.g('delete-btn').click()
    // Confirm dialog (km-popup-confirm) — click the confirm button
    cy.get('[data-test-role="popup-confirm"]', { timeout: 10000 }).click()
  },
}
