/**
 * Knowledge Graph — CRUD contract.
 *
 * Uses a different component tree (CreateGraphDialog instead of CreateNew;
 * separate Playground/RetrievalTestDrawer for preview). data-test attrs
 * added to Page.vue (search-input, new-btn).
 *
 * Details page has name + description + system_name.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Knowledge Graph',
  listRoute: '#/knowledge-graph',
  detailPathSegment: 'knowledge-graph',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  skip: { C4: true, C6: true, C7: true, C8: true },
})
