describe('Prompt templates', () => {
  it('RAG Tool - create', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/rag-tools')
    cy.g('new-btn').click()

    cy.g('Save').click()
    cy.g('popup-confirm').contains('Field can not be empty')

    cy.g('name-input').click()
    cy.g('name-input').km_type()
    cy.g('system_name-input').click()

    cy.g('Save').click()

    cy.g('popup-confirm').contains('RAG Tools knowledge soureces must consist at least 1 source')
    cy.km_select('knowledge-sources', ['Video Test', 'Web for Docs'])

    cy.g('Save').click()
  })

  it('RAG Tool - preview', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/rag-tools')
    cy.g('search-input').click()
    cy.g('search-input').type('R_TEST')
    cy.g('table-row').eq(0).click()
    cy.g('search-input').click()
    cy.g('search-input').type('test')

    cy.intercept('POST', 'http://localhost:8000/rag_tools/test').as('apiCall')

    cy.g('search-btn').click()
    cy.wait('@apiCall').its('response.statusCode').should('eq', 200)
    cy.g('preview-answer').contains('The answer was found using information from the following articles:')
  })

  it('RAG Tool - delete', () => {
    cy.viewport(1920, 1080)
    cy.visit('#/rag-tools')
    cy.g('search-input').click()
    cy.g('search-input').type('e2e-test')
    cy.g('table-row').eq(0).click()
    cy.g('show-more-btn').click()
    cy.g('delete-btn').click()
    cy.g('popup-confirm').contains('You are about to delete the RAG Tool')
    cy.g('Delete RAG Tool').click()
  })
})
