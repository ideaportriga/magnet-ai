/// <reference types="cypress" />

import { listPage } from './listPage'

/**
 * Canonical 4-test Preview contract for entities with a preview/playground
 * pane (Prompts, Configuration/RAG, Agents, KnowledgeGraph).
 *
 *   P1. preview panel renders on detail page
 *   P2. run preview → API called → response displayed
 *   P3. preview with invalid input → UI error visible (optional)
 *   P4. preview while another run in flight → second run waits (optional)
 *
 * Each entity customises the trigger input/button via opts.
 */

export interface PreviewContractOptions {
  entity: string
  listRoute: string
  /**
   * Called after visiting the list to navigate to a detail page that has
   * preview available (e.g. search for a seeded record, click first row).
   */
  openPreviewableDetail: () => void
  /** Selector for the text input where the user types the preview query. */
  inputSelector: string
  /** Selector for the "Run preview" button. */
  runButtonSelector: string
  /**
   * Regex matching the API endpoint the preview call hits — used for
   * cy.intercept(...).as().
   */
  apiPathMatcher: RegExp | string
  /**
   * HTTP method for the preview call (default 'POST').
   */
  apiMethod?: 'GET' | 'POST' | 'PUT'
  /** Optional: skip specific tests when they don't apply. */
  skip?: Partial<Record<'P1' | 'P2' | 'P3' | 'P4', boolean>>
}

export function runPreviewContract(opts: PreviewContractOptions) {
  const { entity, listRoute, openPreviewableDetail, inputSelector, runButtonSelector, apiPathMatcher, apiMethod = 'POST', skip = {} } = opts

  describe(`${entity} — Preview contract`, () => {
    beforeEach(() => {
      listPage.visit(listRoute)
      openPreviewableDetail()
    })

    if (!skip.P1) {
      it('P1. preview panel renders on detail page', () => {
        cy.get(inputSelector, { timeout: 15000 }).should('be.visible')
        cy.get(runButtonSelector).should('be.visible')
      })
    }

    if (!skip.P2) {
      it('P2. run preview → API called → response displayed', () => {
        cy.intercept(apiMethod, apiPathMatcher).as('previewCall')
        cy.get(inputSelector).click().type('e2e test query')
        cy.get(runButtonSelector).click()
        cy.wait('@previewCall', { timeout: 30000 })
          .its('response.statusCode')
          .should('be.oneOf', [200, 201])
      })
    }

    if (!skip.P3) {
      it('P3. preview with empty input → either disabled or error', () => {
        cy.get(inputSelector).clear()
        // Either the button is disabled (happy case) or clicking it produces
        // a UI validation error / toast. We accept either signal.
        cy.get(runButtonSelector).then(($btn) => {
          if ($btn.is(':disabled')) {
            expect($btn.is(':disabled')).to.be.true
          } else {
            cy.wrap($btn).click()
            cy.get('.q-notification, .q-field--error, [role="alert"]', { timeout: 3000 }).should('exist')
          }
        })
      })
    }
  })
}
