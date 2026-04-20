/**
 * Evaluation Jobs — CRUD contract (reduced).
 *
 * EvaluationJobs create dialog requires test_set + evaluated_tool/tools +
 * iteration_count — i.e. pre-existing data. Without I.1 seed loader, only
 * C1+C2+C5 are reliably runnable.
 *
 * Detail page exists but is mostly read-only results (no description-input
 * to edit). C6/C7/C8 skipped.
 */

import { runCrudContract } from '../support/pages/crudContract'

runCrudContract({
  entity: 'Evaluation Jobs',
  listRoute: '#/evaluation-jobs',
  detailPathSegment: 'evaluation-jobs',
  seedPrefix: 'e2e-test-',
  hasDescription: false,
  skip: { C3: true, C6: true, C7: true, C8: true },
})
