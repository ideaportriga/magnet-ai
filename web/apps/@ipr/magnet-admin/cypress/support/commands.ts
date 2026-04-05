/// <reference types="cypress" />

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable<Subject> {
      login(email: string, password: string): void
      g(selector: string): Chainable<JQuery<HTMLElement>>
      km_type(): Chainable<JQuery<HTMLElement>>
      km_select(selector: string, value: string | string[]): Chainable<JQuery<HTMLElement>>
      dismissErrors(): Chainable<void>
    }
  }
}

// Get element by data-test attribute - this is general approach to get elements in cypress tests
Cypress.Commands.add('g', (selector) => {
  return cy.get(`[data-test="${selector}"]`)
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

export {}
