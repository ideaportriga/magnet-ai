/**
 * Prompt Templates — CRUD contract.
 *
 * Supersedes `crud_prompt_templates.cy.ts` + edit cycle tests that were
 * missing. The create dialog requires category selection (select-category)
 * — `advanceCreateSteps` picks the first option.
 *
 * Old spec kept running until this is green in CI, then deleted.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Prompt Templates',
  listRoute: '#/prompt-templates',
  detailPathSegment: 'prompt-templates',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  advanceCreateSteps: () => {
    // Select the first category (required field in the Prompt Template create dialog)
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="select-category"]').length) {
        cy.g('select-category').click()
        cy.get('[data-test="options"]').first().click()
      }
    })
  },
  skip: { C4: true, C6: true, C7: true, C8: true },
})
