/// <reference types="cypress" />

/**
 * Page-object helpers for the "Create new record" dialog.
 *
 * Two shapes of dialog exist in magnet-admin:
 *
 *   A) `km-popup-confirm` based — most entities (Agents, Retrieval, Prompts,
 *      EvaluationSets, EvaluationJobs, ApiKeys, ModelConfig, ...).
 *      The dialog root has `data-test="popup-confirm"`. Save/Cancel buttons
 *      have *two* test attrs:
 *        - `data-test="<ButtonLabel>"` (legacy, e.g. `Save`)
 *        - `data-test-role="popup-confirm" | "popup-cancel"` (stable)
 *
 *   B) Custom `q-dialog` with manual button rows (Collections stepper,
 *      AIApps, Mcp). Buttons tagged with `data-test="save-btn" | "cancel-btn"`
 *      (added via I.2 data-test audit).
 *
 * `createDialog.save()` and `createDialog.cancel()` try both shapes so the
 * helper works for either kind of dialog without the caller caring.
 */

export const createDialog = {
  /**
   * Assert the create dialog is open and one of its action buttons is
   * actually visible (not mid-animation). Pages keep hidden popup-confirm
   * instances in the DOM (delete-confirm, clone, etc.), so we filter to
   * `:visible` and also wait for the name-input (or save-btn for custom
   * dialogs) to be reachable.
   */
  expectOpen() {
    // Step 1: a visible dialog exists
    cy.get('.q-dialog--modal, [data-test="popup-confirm"]', { timeout: 15000 })
      .filter(':visible')
      .should('have.length.gte', 1)
    // Step 2: wait for an interactive element inside the dialog (ride out
    // the fade-in animation so subsequent clicks don't miss).
    cy.get(
      '[data-test-role="popup-confirm"]:visible, [data-test="save-btn"]:visible, [data-test="next-btn"]:visible',
      { timeout: 15000 },
    ).should('have.length.gte', 1)
  },

  /**
   * Fill the `name-input` field with a random e2e-test-* value.
   * Filters to visible instance — pages often have hidden name-inputs on
   * the detail page behind the dialog.
   */
  fillRandomName(prefix = 'e2e-test-') {
    cy.get('[data-test="name-input"]:visible', { timeout: 10000 }).first().then(($el) => {
      const $input = $el.is('input') ? $el : $el.find('input')
      const rand = Math.random().toString(36).slice(2, 8)
      cy.wrap($input).clear().type(`${prefix}${rand}`)
    })
  },

  /** Fill an arbitrary value into a named input. */
  fillField(dataTest: string, value: string) {
    cy.get(`[data-test="${dataTest}"]:visible`).first().find('input').clear().type(value)
  },

  /** Click Save — tries stable role first, then legacy label. Always filter to visible. */
  save() {
    cy.get('body').then(($body) => {
      const stable = $body.find('[data-test-role="popup-confirm"]:visible')
      const generic = $body.find('[data-test="save-btn"]:visible')
      if (stable.length) cy.wrap(stable).first().click()
      else if (generic.length) cy.wrap(generic).first().click()
      else cy.get('[data-test="Save"]:visible').first().click()
    })
  },

  /** Click Cancel — tries stable role first, then legacy label, then custom. */
  cancel() {
    cy.get('body').then(($body) => {
      const stable = $body.find('[data-test-role="popup-cancel"]:visible')
      const generic = $body.find('[data-test="cancel-btn"]:visible')
      if (stable.length) cy.wrap(stable).first().click()
      else if (generic.length) cy.wrap(generic).first().click()
      else cy.get('[data-test="Cancel"]:visible').first().click()
    })
  },

  /** Assert a validation message is visible in the dialog. */
  expectValidationError() {
    cy.get('.q-field--error, [role="alert"]', { timeout: 5000 }).should('exist')
  },
}
