/// <reference types="cypress" />

/**
 * Page-object helpers for the entity list page.
 *
 * Assumes the page follows the standard admin layout:
 *   [search-input] [new-btn]  at top
 *   [km-data-table] with rows having `data-test="table-row"` (set in
 *   packages/ui-comp/src/components/base/DataTable.vue)
 *
 * Methods return `cy.Chainable` where useful so callers can add assertions.
 */

export interface VisitListOptions {
  /** Skip waiting for search-input (set to false for card-grid pages without search) */
  hasSearch?: boolean
}

export const listPage = {
  /** Navigate to the route and wait for the app shell to render. */
  visit(route: string, opts: VisitListOptions = {}) {
    const { hasSearch = false } = opts
    cy.viewport(1920, 1080)
    cy.visit(route)
    cy.dismissErrors()
    // Some list pages hide search-input until rows exist (mcp, knowledge_graph,
    // api_servers, model_config show an empty-state instead). Callers that
    // actually need search must pass `hasSearch: true` or use listPage.search
    // which has its own 15s timeout.
    if (hasSearch) {
      cy.g('search-input', { timeout: 15000 }).should('be.visible')
    } else {
      cy.get('.q-page, .q-layout', { timeout: 15000 }).should('exist')
    }
  },

  /** Type into the search input and wait out the 300ms debounce in useDataTable. */
  search(query: string) {
    // Search input is disabled during the initial data fetch; wait a generous
    // timeout before clearing/typing.
    cy.g('search-input', { timeout: 15000 }).find('input', { timeout: 15000 }).should('not.be.disabled')
    cy.g('search-input').find('input').clear().type(query)
    cy.wait(500) // §D.2 debounce + small buffer
  },

  /** Clear search (works with clearable km-input). */
  clearSearch() {
    cy.g('search-input').find('input').clear()
    cy.wait(500)
  },

  /** Click the "+ New" button to open the create dialog. */
  clickNew() {
    cy.g('new-btn').should('be.visible').click()
  },

  /**
   * Assert at least one table row is visible (use after search for a seed
   * prefix, so we know the filter matched something).
   */
  expectAtLeastOneRow() {
    cy.g('table-row', { timeout: 10000 }).should('have.length.gte', 1)
  },

  /** Assert exactly zero rows (e.g. after deleting the only match). */
  expectNoRows() {
    cy.g('table-row').should('have.length', 0)
  },

  /** Assert every visible row contains the given text (case-insensitive). */
  expectAllRowsContain(text: string) {
    cy.g('table-row').each(($row) => {
      expect($row.text().toLowerCase()).to.include(text.toLowerCase())
    })
  },

  /** Click the first row → navigates to detail page. */
  openFirstRow() {
    cy.g('table-row', { timeout: 10000 }).first().click()
  },

  /** Click a row whose cell text matches `name`. */
  openRowByName(name: string) {
    cy.g('table-row').contains(name).click()
  },
}
