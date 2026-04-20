/**
 * API Servers — CRUD contract.
 *
 * Create dialog is km-popup-confirm with name/system_name/url. All three
 * inputs tagged via I.2 audit. Detail page has name + system_name, no
 * description — C6/C7 skipped.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'API Servers',
  listRoute: '#/api-servers',
  detailPathSegment: 'api-servers',
  seedPrefix: 'e2e-test-',
  hasDescription: false,
  advanceCreateSteps: () => {
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="url-input"]').length) {
        cy.g('url-input').find('input').clear().type('http://localhost:9000')
      }
    })
  },
  skip: { C6: true, C7: true, C4: true, C8: true },
})
