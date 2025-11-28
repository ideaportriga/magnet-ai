describe("AI Apps", () => {
  it("tests CreateAI App", () => {
    cy.viewport(1920, 1080);
    cy.visit("#/ai-apps");
    cy.g("new-btn").click();
    cy.g('name-input').click();
    cy.g('name-input').km_type();
    cy.g('system_name-input').click();
    cy.g('Save').click();
  });
});

