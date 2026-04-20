/**
 * API Keys — CRUD contract (reduced).
 *
 * API Keys has NO detail route — only a list page with a two-step create
 * dialog (step 0: name + create; step 1: display generated key + copy).
 * The standard contract's detail-based tests (C5/C6/C7/C8) don't apply.
 *
 * Write a tailored spec instead of using runCrudContract.
 */

import { listPage } from '../support/pages/listPage'

describe('API Keys — list + create', () => {
  it('C1. list page renders', () => {
    listPage.visit('#/api-keys')
    cy.get('.km-data-table', { timeout: 15000 }).should('exist')
  })

  it('C2. search filters the list', () => {
    listPage.visit('#/api-keys')
    listPage.search('e2e-test-')
    cy.g('search-input').find('input').should('have.value', 'e2e-test-')
  })

  it('C3. create — empty name → Create button disabled', () => {
    listPage.visit('#/api-keys')
    listPage.clickNew()
    // On empty name the create-btn wrapper has data-disabled="true"
    cy.g('create-btn', { timeout: 5000 })
      .should('have.attr', 'data-disabled', 'true')
  })

  it('C4. create API key — fill name → Create → step 1 shows the key', () => {
    listPage.visit('#/api-keys')
    listPage.clickNew()
    cy.g('name-input', { timeout: 10000 }).find('input')
      .type(`e2e-test-${Math.random().toString(36).slice(2, 8)}`)
    cy.g('create-btn').click()
    // Step 1: km-btn "Done" — km-btn renders as .km-button div, not <button>.
    cy.contains(/^Done$/, { timeout: 10000 }).should('be.visible')
  })
})
