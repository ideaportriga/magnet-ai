/**
 * Retrieval Tools — CRUD contract.
 *
 * Retrieval uses a simple `km-popup-confirm` dialog (single step, no stepper)
 * so `advanceCreateSteps` is unneeded. The name-input/system-name-input
 * data-test attrs were added via I.2 audit.
 *
 * C6/C7 (edit description) rely on `description-input` on the detail page
 * header (added by the I.2 audit on Retrieval/details.vue).
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Retrieval Tools',
  listRoute: '#/retrieval',
  detailPathSegment: 'retrieval',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  // Create requires knowledge-sources selection (FK constraint); without
  // the I.1 seed loader, C4/C6/C7/C8 can't get a happy-path create.
  skip: { C4: true, C6: true, C7: true, C8: true },
})
