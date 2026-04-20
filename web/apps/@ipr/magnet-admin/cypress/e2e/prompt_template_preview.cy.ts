/**
 * Prompt Template — Preview contract.
 *
 * Supersedes the preview case in legacy `prompt_template.cy.ts`.
 * Requires a seeded prompt template (search `e2e-test-` or a known
 * well-known prompt like `R_F_SYSTEM`). Relies on I.1 seed loader once
 * landed; for now assumes at least one row exists.
 */

import { runPreviewContract } from '../support/pages/previewContract'
import { listPage } from '../support/pages/listPage'

runPreviewContract({
  entity: 'Prompt Templates',
  listRoute: '#/prompt-templates',
  openPreviewableDetail: () => {
    listPage.search('e2e-test-')
    cy.get('body').then(($body) => {
      if ($body.find('[data-test="table-row"]').length) {
        listPage.openFirstRow()
      } else {
        // Fallback: any known preview-enabled prompt
        listPage.clearSearch()
        listPage.openFirstRow()
      }
    })
  },
  inputSelector: '[data-test="preview-input"]',
  runButtonSelector: '[data-test="preview-btn"]',
  apiPathMatcher: /\/prompt_templates\/(test|.+\/preview)/,
  apiMethod: 'POST',
  skip: { P4: true }, // no in-flight guard test yet
})
