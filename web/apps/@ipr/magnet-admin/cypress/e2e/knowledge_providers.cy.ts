/**
 * Knowledge Providers — CRUD contract.
 *
 * List page renders via nested `knowledge-providers-table` component; data-test
 * attrs added to Table.vue (search-input, new-btn). Create dialog requires
 * a source type (select-type) — advanceCreateSteps picks first option.
 *
 * Detail page has name + system_name, NO description — C6/C7 skipped.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Knowledge Providers',
  listRoute: '#/knowledge-providers',
  detailPathSegment: 'knowledge-providers',
  seedPrefix: 'e2e-test-',
  hasDescription: false,
  advanceCreateSteps: () => {
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="select-type"]').length) {
        cy.g('select-type').click()
        cy.get('[data-test="options"]').first().click()
      }
    })
  },
  skip: { C6: true, C7: true, C4: true, C8: true },
})
