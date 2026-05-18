/**
 * Re-capture admin (RBAC) screenshots.
 *
 * The router has a `beforeEach` guard that redirects to `/` (→ /agents)
 * when `authStore.userInfo` is empty. Hard-visiting an admin route races
 * the guard against /api/v2/auth/me, so we land on /profile (no permission
 * required), wait for /auth/me to populate userInfo, then update
 * `window.location.hash` to trigger an in-app navigation that the guard
 * now lets through.
 */

const PAGES: { route: string; name: string }[] = [
  { route: '/admin/users', name: 'admin-users-list' },
  { route: '/admin/roles', name: 'admin-roles-list' },
  { route: '/admin/access-log', name: 'admin-access-log' },
]

describe('Admin RBAC documentation screenshots', () => {
  PAGES.forEach(({ route, name }) => {
    it(`captures ${name} (${route})`, () => {
      cy.viewport(1600, 1000)
      cy.intercept('GET', '**/api/v2/auth/me').as('authMe')

      cy.visit('#/profile')
      cy.wait('@authMe', { timeout: 15000 })
      cy.get('#app', { timeout: 15000 }).should('exist')

      // Hash-change navigation: no page reload, auth store stays populated.
      cy.window().then((win) => {
        win.location.hash = `#${route}`
      })

      cy.hash().should('eq', `#${route}`)
      // Settle async tables (users/roles/audit-log). No selector assertion —
      // it tripped earlier runs and tainted screenshots with the failure overlay.
      cy.wait(2500)
      cy.screenshot(`docs/${name}`, { capture: 'viewport', overwrite: true })
    })
  })
})
