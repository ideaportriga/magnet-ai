Application architecture 

## Technologies and Dependencies

- Lightstar  
- SQLAlchemy Core  
- Pydantic  
- Alembic  
- asyncpg / cx_Oracle / aiosqlite / pyodbc  



## Entities

### Prompt Template
- **Description**: A query template for AI that can include variables and static text.

### Knowledge Source
- **Description**: A knowledge source that can be used for RAG (Retrieval-Augmented Generation).

### RAG Tool
- **Description**: A tool for extracting information from a Knowledge Source and constructing queries to the AI.

### AI App
- **Description**: An application that uses AI to perform tasks such as text generation, data analysis, etc.

### Retrieval Tool
- **Description**: A tool for retrieving data from a knowledge base or other data sources.

### Agent
- **Description**: An agent that manages interaction with the AI, including processing requests, managing state, and performing actions based on AI responses.

### LLM Model
- **Description**: An AI model that can be used to perform tasks such as text generation, classification, etc.

### API Tool
- **Description**: A tool for interacting with external APIs, which can be used to fetch data or perform actions based on AI requests.

### Collection
- **Description**: A collection that contains texts and vector representations for use with AI.

### Evaluation Set
- **Description**: A set of test data for evaluating AI performance.

### Evaluations
- **Description**: The results of AI evaluation based on the Evaluation Set.

### Jobs
- **Description**: Background jobs

### Metrics
- **Description**: Metrics collected to evaluate AI and other component performance.

### Traces
- **Description**: Traces collected for performance analysis and debugging of AI and other components.


