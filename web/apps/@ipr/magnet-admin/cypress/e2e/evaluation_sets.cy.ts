/**
 * Evaluation Sets — CRUD contract.
 *
 * Create dialog is km-popup-confirm with name/system_name + Type select
 * (required). `advanceCreateSteps` picks the first type option.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Evaluation Sets',
  listRoute: '#/evaluation-sets/',
  detailPathSegment: 'evaluation-sets',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  advanceCreateSteps: () => {
    // Select the Type (required field in EvaluationSets create dialog)
    cy.get('body').then(($body) => {
      const typeSelect = $body.find('[data-test="typeRef"], [ref="typeRef"]')
      if (typeSelect.length) {
        cy.wrap(typeSelect.first()).click()
        cy.get('[data-test="options"]').first().click()
      }
    })
  },
  skip: { C4: true, C6: true, C7: true, C8: true },
})
