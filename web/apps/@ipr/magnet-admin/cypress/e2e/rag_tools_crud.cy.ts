/**
 * RAG Tools (Configuration) — CRUD contract.
 *
 * Replaces/supersedes the partial `crud_rag_tools.cy.ts` and `rag_tool.cy.ts`
 * files with the canonical 8-test contract. Those older files will be
 * removed once this spec is green in CI.
 *
 * RAG Tools' create dialog requires at least one Knowledge Source to be
 * selected to pass validation. On an empty dev DB C3 validation triggers
 * both on name + on knowledge-sources. C4 happy-path will fail without
 * seeded Knowledge Sources — skip C4/C6/C7/C8 until I.1 fixtures landed.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'RAG Tools',
  listRoute: '#/rag-tools',
  detailPathSegment: 'rag-tools',
  seedPrefix: 'e2e-test-',
  hasDescription: true,
  // Dialog requires knowledge-sources select to pass validation — without
  // seeded data, C4/C6/C7/C8 will fail on create step. Mark skip until
  // I.1 seed loader is landed (see E2E_CRUD_PREVIEW_ROADMAP.md §I.1).
  skip: { C6: true, C7: true, C8: true, C4: true },
})
