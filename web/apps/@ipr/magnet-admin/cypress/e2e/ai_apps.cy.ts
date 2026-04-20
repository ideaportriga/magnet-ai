/**
 * AI Apps — CRUD contract.
 *
 * AIApps is a card-grid list (not km-data-table); cards tagged
 * data-test="table-row" via I.2 audit. Create dialog is km-popup-confirm
 * with name + system_name. Detail page has description field.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'AI Apps',
  listRoute: '#/ai-apps',
  detailPathSegment: 'ai-apps',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  skip: { C4: true, C6: true, C7: true, C8: true },
})
