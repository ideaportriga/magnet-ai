/// <reference types="cypress" />

// ***********************************************
// This example commands.ts shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable<Subject> {
      login(email: string, password: string): void
      g(selector: string): Chainable<JQuery<HTMLElement>>
      km_type(): Chainable<JQuery<HTMLElement>>
      km_select(selector: string, value: string | string[]): Chainable<JQuery<HTMLElement>>
    }
  }
}

// Get element by data-test attribute - this is general approach to get elements in cypress tests
Cypress.Commands.add('g', (selector) => {
  return cy.get(`[data-test="${selector}"]`)
})

// Type random string into input
Cypress.Commands.add('km_type', { prevSubject: 'element' }, (subject) => {
  const randomString = Math.random().toString(36).substring(7)
  return cy.wrap(subject).type(`e2e-test-${randomString}`)
})

// Select from dropdown by text array
// 1. Find select element
// 2. Find all options
// 3. Iterate over options and click on the one that matches the text or list of texts
// 4. Click on the option

Cypress.Commands.add('km_select', (selector, value) => {
  return cy.get(`[data-test="${selector}"]`).then(($el) => {
    cy.wrap($el).click()
    cy.get('[data-test="options"]').each(($el) => {
      // value is an array of strings or a single string
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

export {}
