Collections: 
- agent_conversation
- agents
- ai_app
- api_tools 
- assistant_tools 
- assistants ?
- cases ?
- collections 
- conversations
- documents_
- evaluation_jobs 
- evaluation_sets
- evaluations 
- jobs 
- jobs_running 
- jobs_test
- metrics
- models
- observations
- prompts
- rag_cache ? 
- rag_config ?
- rag_tool_test_set ?
- rag_tools
- retrieval_tools 
- templates 
- traces 



















You are a highly skilled database expert. I am migrating data from a MongoDB collection to a PostgreSQL database. I will provide an example document from a MongoDB collection. Your task is to create a `schema.sql` file that defines the necessary PostgreSQL tables to store the information from the example document. Follow these guidelines:

1. Analyze the structure and data types of the provided MongoDB document.
2. Create appropriate PostgreSQL tables with proper columns, data types, and constraints (e.g., primary keys, foreign keys, NOT NULL, etc.).
3. Handle nested objects and arrays in the document by creating related tables or using PostgreSQL JSONB/JSON types where appropriate.
4. Include comments in the SQL to explain the purpose of tables and columns.
5. If the document contains fields that imply relationships, define foreign key constraints.
6. Use standard SQL syntax compatible with PostgreSQL.
7. Create sql file in same dirctory as .md file with json data. Name the file same as the .md file but with .sql extension.


**Workspace: Collecting workspace information. Filtering to the most relevant information.**

Below is an approximate step-by-step plan for migrating from MongoDB to SQL using advanced-alchemy (SQLAlchemy 2.0+ async ORM). The estimation is based on ~18 entities from the entities folder. Time is indicated in person-weeks (p-w).

1. **Preparation Stage (1 p-w)**  
   - Gather requirements and analyze the current MongoDB implementation  
   - Inventory entities in the entities folder  

2. **SQL Schema and Model Design (2 p-w)**  
   - Convert SQL scripts (e.g., api_tools.sql) into advanced-alchemy models  
   - Define relationships, indexes, and constraints  

3. **ORM Model Development (3 p-w)**  
   - Create Pydantic/SQLModel classes or SQLAlchemy Declarative models for each entity (~1 model/day)  
   - Configure migrations (Alembic)  

4. **Repository and Service Layer Implementation (2 p-w)**  
   - Develop a unified CRUD interface using async repositories  
   - Migrate business logic to services  

5. **Data Migration (1–2 p-w)**  
   - Write ETL scripts: read from MongoDB → insert into PostgreSQL  
   - Perform validation and deduplication  

6. **API and Frontend Adaptation (2 p-w)**  
   - Redesign FastAPI routes and DTOs for new models  
   - Update frontend queries (typing, new fields)  

7. **Testing and QA (2 p-w)**  
   - Write unit/integration tests for repositories and API  
   - Run end-to-end scenarios  

8. **Deployment and Stabilization (1 p-w)**  
   - Configure CI (Alembic, tests)  
   - Monitor and fix bugs  

**Total: ~14–15 person-weeks (~3.5 months)**, including a buffer for unforeseen tasks and modeling. The estimate can be adjusted proportionally if the number of entities or complexity of logic increases.