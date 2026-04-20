/**
 * MCP Servers — CRUD contract.
 *
 * Create dialog is a q-dialog (not km-popup-confirm) with name, system_name,
 * url, and transport radio. data-test attrs added on all three inputs via
 * I.2 audit. Detail page has name + system_name (no description — C6/C7
 * skipped).
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'MCP Servers',
  listRoute: '#/mcp',
  detailPathSegment: 'mcp',
  seedPrefix: 'e2e-test-',
  hasDescription: false,
  advanceCreateSteps: () => {
    // URL is required (otherwise create fails). Fill a dummy URL.
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="url-input"]').length) {
        cy.g('url-input').find('input').clear().type('http://localhost:9999/mcp')
      }
    })
  },
  skip: { C6: true, C7: true, C4: true, C8: true },
})
