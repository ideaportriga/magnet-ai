# Code Migration Process to SQLAlchemy

- ## Requirements
- Use SQLAlchemy for database interactions
- The solution must support asynchronous database access
- Code should be the same for all supported DBMS (Postgres, Oracle)
- Use Pydantic for data validation and serialization
- Use repositories for data access abstraction
- Use Alembic for database migrations

- Optional:
- Add users and roles
- Support real-time data updates (e.g., via WebSocket or Server-Sent Events)
- Use fixtures to load initial data
- Migrate existing data from MongoDB to the relational database
- Support additional DBMS (e.g., MySQL, SQLite)

- ## Estimation

- ### Analysis

- + 1. Selection of solution and architecture
-   - Use SQLAlchemy Core for database interactions
-   - Support asynchronous access via asyncpg for Postgres and other libraries for other DBMS
-   - Repositories for data access abstraction
-   - Services (advanced-alchemy) for CRUD operations
-   - Pydantic for data validation and serialization
-   - Alembic for database migrations
- + 2. Analyze current schemas and entities
- (1d) 3. Design relational models
- (1d) 4. Develop a new approach for displaying metrics and traces
- (+) 5. Use fixtures to load initial data
- (?) 6. Add users and roles
- (+) 7. Migrate existing data from MongoDB to the relational database
- (?) 8. Support real-time data updates (e.g., via WebSocket or Server-Sent Events)
- (?) 9. Ability to use gql for frontend integration (SQLAlchemy supports a plugin for creating gql)


- ### Development

- + 1. Add SQLAlchemy usage to the project
- + 2. Rewrite CRUD operations using SQLAlchemy
-(1d) 3. Rewrite business logic using repositories
-(3d) 4. Rewrite reports using SQLAlchemy
- + 5. Add Alembic for database schema migrations
-(1d) 6. Rewrite the scheduler store using SQLAlchemy
-(1d) 7. Add fixtures for loading initial data
-(1d) 8. Write scripts to migrate existing data from MongoDB to the relational database
-(?) 9. Add schema for analytical data (events)

# Additional
- 1. Refactor retrieve schema to use variants
- 2. Improve the UI to accommodate the new data structure
   - retrieval
   - models (model field)
- 3. Issue with obtaining the current session in routes: passing db_session


### Testing
-(3d) 1. Conduct testing


Total estimate: 15 days