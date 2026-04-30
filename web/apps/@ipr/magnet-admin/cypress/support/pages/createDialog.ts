/// <reference types="cypress" />

/**
 * Page-object helpers for the "Create new record" dialog.
 *
 * Two shapes of dialog exist in magnet-admin:
 *
 *   A) `km-popup-confirm` based — most entities (Agents, Retrieval, Prompts,
 *      EvaluationSets, EvaluationJobs, ApiKeys, ModelConfig, ...).
 *      Current DS-backed dialogs expose `data-test="ds-alert-dialog"` or
 *      `data-test="km-popup-confirm"`; actions use stable DS or popup-confirm
 *      data-test hooks.
 *
 *   B) Custom `km-dialog` with manual button rows (Collections stepper,
 *      AIApps, Mcp). Buttons tagged with `data-test="save-btn" | "cancel-btn"`
 *      (added via I.2 data-test audit).
 *
 * `createDialog.save()` and `createDialog.cancel()` try both shapes so the
 * helper works for either kind of dialog without the caller caring.
 */

export const createDialog = {
  confirmSelector: '[data-test-role="popup-confirm"]:visible, [data-test="ds-alert-dialog-confirm"]:visible, [data-test^="popup-confirm-"]:not([data-test^="popup-confirm-cancel-"]):not([data-test^="popup-confirm-secondary-"]):visible',
  cancelSelector: '[data-test-role="popup-cancel"]:visible, [data-test="ds-alert-dialog-cancel"]:visible, [data-test^="popup-confirm-cancel-"]:visible',

  /**
   * Assert the create dialog is open and one of its action buttons is
   * actually visible (not mid-animation). Pages keep hidden popup-confirm
   * instances in the DOM (delete-confirm, clone, etc.), so we filter to
   * `:visible` and also wait for the name-input (or save-btn for custom
   * dialogs) to be reachable.
   */
  expectOpen() {
    // Step 1: a visible dialog exists. Include `km-dialog` (custom-stepper
    // dialogs like Collections wrap content in `<km-dialog>` instead of
    // `<km-popup-confirm>`) and `cancel-btn` (always present, even before
    // the next/save row renders).
    cy.get('[data-test="km-dialog"], [data-test="km-popup-confirm"], [data-test="ds-alert-dialog"], [data-test="ds-dialog"], [data-test="save-btn"], [data-test="next-btn"], [data-test="cancel-btn"]', { timeout: 15000 })
      .filter(':visible')
      .should('have.length.gte', 1)
    // Step 2: wait for an interactive element inside the dialog (ride out
    // the fade-in animation so subsequent clicks don't miss).
    cy.get(
      `${createDialog.confirmSelector}, [data-test="save-btn"]:visible, [data-test="next-btn"]:visible, [data-test="cancel-btn"]:visible`,
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

  /** Click Save — combines every known confirm hook into a single retried
   *  selector. Single `cy.get` lets cypress retry while the dialog finishes
   *  rendering or re-rendering (e.g. after a select-item picks a category
   *  and the form validation re-paints). Includes:
   *    - DS alert-dialog confirm (`ds-alert-dialog-confirm`)
   *    - popup-confirm role / label-prefixed actions
   *    - generic `save-btn` (custom km-dialog footers)
   *    - stepper `next-btn` (Collections-style step 0 → step 1 advance)
   */
  save() {
    cy.get(
      [
        '[data-test-role="popup-confirm"]:visible',
        '[data-test="ds-alert-dialog-confirm"]:visible',
        '[data-test^="popup-confirm-"]:not([data-test^="popup-confirm-cancel-"]):not([data-test^="popup-confirm-secondary-"]):visible',
        '[data-test="save-btn"]:visible',
        '[data-test="next-btn"]:visible',
      ].join(', '),
      { timeout: 10000 },
    ).first().click()
  },

  /** Click Cancel — tries stable role first, then legacy label, then custom. */
  cancel() {
    cy.get('body').then(($body) => {
      const stable = $body.find(createDialog.cancelSelector)
      const generic = $body.find('[data-test="cancel-btn"]:visible')
      if (stable.length) cy.wrap(stable).first().click()
      else if (generic.length) cy.wrap(generic).first().click()
      else cy.get('[data-test="Cancel"]:visible').first().click()
    })
  },

  /** Assert a validation message is visible in the dialog. */
  expectValidationError() {
    cy.get('[role="alert"], [aria-invalid="true"]', { timeout: 5000 }).should('exist')
  },
}
