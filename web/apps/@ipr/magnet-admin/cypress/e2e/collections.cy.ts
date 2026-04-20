/**
 * Collections (Knowledge Sources) — CRUD contract.
 *
 * Reference implementation for the 8-test contract defined in
 * docs/E2E_CRUD_PREVIEW_ROADMAP.md. Other Tier-1/Tier-2 entities follow
 * the same pattern via `runCrudContract`.
 *
 * Note: Collections uses a 4-step stepper (Basic → Chunking → Indexing →
 * Schedule) — `advanceCreateSteps` clicks through "Next" three times before
 * reaching the Save button. The stepper validates per step, so empty-field
 * validation (C3) is caught on step 0 before we even reach step 3.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Collections',
  listRoute: '#/knowledge-sources/',
  detailPathSegment: 'knowledge-sources',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  advanceCreateSteps: () => {
    // 4-step stepper: Next → Next → Next → Save
    cy.get('body').then(($body) => {
      const count = $body.find('[data-test="next-btn"]').length
      // Click Next until Save button appears (max 3 times)
      for (let i = 0; i < 3; i++) {
        cy.get('body').then(($b) => {
          if ($b.find('[data-test="next-btn"]').length > 0) {
            cy.g('next-btn').first().click()
          }
        })
      }
    })
  },
  skip: { C4: true, C6: true, C7: true, C8: true },
})
