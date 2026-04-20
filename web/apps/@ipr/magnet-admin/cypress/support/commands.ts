/// <reference types="cypress" />

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable<Subject> {
      login(email: string, password: string): void
      g(selector: string, options?: Partial<Cypress.Timeoutable & Cypress.Loggable & Cypress.Withinable>): Chainable<JQuery<HTMLElement>>
      km_type(): Chainable<JQuery<HTMLElement>>
      km_select(selector: string, value: string | string[]): Chainable<JQuery<HTMLElement>>
      dismissErrors(): Chainable<void>
      /**
       * Call the backend `/api/test/cleanup` endpoint to delete all records
       * across known CRUD tables whose `name` or `system_name` begins with
       * the given prefix. Returns the per-table rowcount map.
       * Requires backend to run with `DEBUG_MODE=true`.
       */
      cleanup(prefix?: string): Chainable<{ prefix: string; deleted: Record<string, number> }>
    }
  }
}

// Get element by data-test attribute - this is general approach to get elements in cypress tests
Cypress.Commands.add('g', (selector, options) => {
  return cy.get(`[data-test="${selector}"]`, options)
})

// Type a random e2e-test-* string into an input.
// Works with both <input> elements and km-input wrappers (finds the nested <input>).
Cypress.Commands.add('km_type', { prevSubject: 'element' }, (subject) => {
  const randomString = Math.random().toString(36).substring(7)
  const $input = subject.is('input') ? subject : subject.find('input')
  return cy.wrap($input).clear().type(`e2e-test-${randomString}`)
})

// Select from dropdown by text array
Cypress.Commands.add('km_select', (selector, value) => {
  return cy.get(`[data-test="${selector}"]`).then(($el) => {
    cy.wrap($el).click()
    cy.get('[data-test="options"]').each(($el) => {
      if (Array.isArray(value)) {
        if (value.includes($el.text().trim())) {
          cy.wrap($el).click()
        }
      } else {
        if (value === $el.text().trim()) {
          cy.wrap($el).click()
        }
      }
    })
  })
})

// Dismiss the km-error-dialog if visible.
// The dialog has class .error-dialog and an OK button (q-btn with v-close-popup).
Cypress.Commands.add('dismissErrors', () => {
  cy.get('body').then(($body) => {
    const errorDialog = $body.find('.error-dialog')
    if (errorDialog.length > 0) {
      // Click the OK button inside the error dialog
      const okBtn = errorDialog.find('button').filter((_, el) => {
        return el.textContent?.trim() === 'OK'
      })
      if (okBtn.length > 0) {
        cy.wrap(okBtn.first()).click({ force: true })
        cy.wait(300)
      }
    }
  })
})

// Call the backend cleanup endpoint. Swallows failures (404 = DEBUG_MODE off,
// 5xx = backend issue) so tests still run when the endpoint is unavailable
// — they just leak `e2e-test-*` rows until the next manual wipe.
//
// Note: no cy.* calls inside the .then — mixing synchronous returns with
// queued cy commands breaks Cypress's flow inside `after()` hooks ("invoked
// cy commands but returned a synchronous value").
Cypress.Commands.add('cleanup', (prefix = 'e2e-test-') => {
  return cy
    .request({
      method: 'POST',
      url: `https://localhost:7001/test/cleanup?prefix=${encodeURIComponent(prefix)}`,
      failOnStatusCode: false,
    })
    .then((res) => {
      if (res.status >= 400) {
        return { prefix, deleted: {} } as { prefix: string; deleted: Record<string, number> }
      }
      return res.body as { prefix: string; deleted: Record<string, number> }
    })
})

export {}
