/**
 * Agents — CRUD contract.
 *
 * Agent creation is a simple km-popup-confirm (name + system_name). The
 * detail page has nested tabs (topics, post-processing, settings,
 * conversations, notes) — edit/save/revert test uses the description
 * field in the header, same as other entities.
 *
 * AGENT list page renders a card grid (not km-data-table). Cards have
 * data-test="table-row" (added via I.2 audit).
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Agents',
  listRoute: '#/agents',
  detailPathSegment: 'agents',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  skip: { C4: true, C6: true, C7: true, C8: true },
})
