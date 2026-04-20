/**
 * RAG Tools — Preview contract.
 *
 * The RAG tool detail page hosts the `search-prompt` component inside
 * Configuration/Drawer.vue, which already carries `data-test="search-input"`
 * and `data-test="search-btn"` (ui-comp/Search/Prompt.vue).
 *
 * Requires a seeded RAG tool (real test needs at least one e2e-test-* or
 * pre-existing rag tool — without I.1 seed loader, this spec falls back to
 * picking any first row).
 */

import { runPreviewContract } from '../support/pages/previewContract'
import { listPage } from '../support/pages/listPage'

runPreviewContract({
  entity: 'RAG Tools',
  listRoute: '#/rag-tools',
  openPreviewableDetail: () => {
    cy.get('[data-test="table-row"]', { timeout: 15000 }).first().click({ force: true })
    cy.url({ timeout: 15000 }).should('match', /rag-tools\/[a-f0-9-]{8,}/)
    cy.wait(800)
  },
  inputSelector: '[data-test="search-input"]',
  runButtonSelector: '[data-test="search-btn"]',
  apiPathMatcher: /\/rag_tools\/(ask|test)/,
  apiMethod: 'POST',
  // P2 hits the real RAG ask endpoint which can take 30+ seconds and
  // depends on a configured RAG pipeline — skip until a deterministic
  // fixture is available.
  skip: { P2: true, P3: true, P4: true },
})
