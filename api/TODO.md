

## Technical debt



### API Naming

Reference:
https://github.com/team-monite/api-style-guide/blob/main/Guidelines.md


Main goal - unify naming in API (path segments, query params, body fields)

Proposal - use snake_case for all of them


Actions by priorities:
1) Endpoints that we are sharing with API consumers
*IMPORTANT: verify that it will not brake anything for existing API consumers (sync with the team)*

DONE. Old routes kept for backward compatibility and will be removed later

[X] /rag-tools/execute
  - rename path
[X] prompt-templates/execute
  - rename path
  - rename body fields
[X] code -> system_name (in API first, but also consider renaming in backend code and database)


2) Review all other routes and create plan for incremental naming unification
Path segments will be fixed in step 1

[ ] Unify field names (both case and semantics) in  Request and response body
  e.g.:
  - userMessage -> user_message
  - prompt_template_system_name - prompt_template


### Auth
- [ ] use before_request for auth in order not to decorate every single route handler except few
- [ ] request.auth_data in auth.py - explore other options to pass data to request handlers
- [ ] use login_hint
- [ ] use nonce

### Azure OpenAI

- [ ] Explore Networking setup options
- [ ] Create content filter

### Validation 

- [ ] Validate input and output data in request all routes 
- [ ] Validate input and output data only for 3rd party services (service - is a atomic operation that can be reused in different places)

### Refactoring

- [ ] Refactor routes: elinminating code duplication and cleaning up the code (sqlight, chroma)
- [ ] Use one pattern for validation input and output data in all routes (use @validate decorator)

### Testing

- [ ] Add tests for all routes
- [ ] Add tests for all services
- [ ] Add tests for all flows

### Some other stuff

- [ ] Services folder has to contain only services 
- [ ] Transfer flows to flows folder

### Ideas for future improvements

- [ ] Add some flow library to simplify flow creation and usage 
Flows libraries has some build in advantages as retries, timeouts, logging, parallel execution, etc. 


### Linting, formatting

- [ ] Consider using Ruff

