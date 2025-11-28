describe("Prompt templates", () => {
  it("Prompt template - create", () => {
    cy.viewport(1920, 1080);
  
    cy.visit("#/prompt-templates");
    cy.g('new-btn').click();
    cy.g("Save").click();
    cy.g("popup-confirm").contains("Field can not be empty");
    cy.g("name-input").click();
    cy.g("name-input").km_type();
    cy.km_select("select-category", "RAG");
    cy.g("Save").click();
  });

  it("Prompt template - preview", () => {
    cy.viewport(1920, 1080);
    cy.visit("#/prompt-templates");
    cy.g('search-input').click();
    cy.g('search-input').type('R_F_SYSTEM');
    cy.g('table-row').eq(0).click();
    cy.g('preview-input').click();
    cy.g('preview-input').type('test');

    cy.intercept('POST', 'http://localhost:8000/prompt_templates/test').as('apiCall');

    cy.g('preview-btn').click();
    cy.wait('@apiCall').its('response.statusCode').should('eq', 200);
  });

  it("Prompt template - delete", () => {
    cy.viewport(1920, 1080);
    cy.visit("#/prompt-templates");
    cy.g('search-input').click();
    cy.g('search-input').type('e2e-test-');
    cy.g('table-row').eq(0).click();
    cy.g('show-more-btn').click();
    cy.g('delete-btn').click();
    cy.g('popup-confirm').contains('You are about to delete the Prompt Template');
    cy.g('Delete Prompt Template').click();
  });


});

