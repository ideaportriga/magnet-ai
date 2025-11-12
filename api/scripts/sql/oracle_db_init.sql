SET DEFINE OFF;

CREATE USER AIUSER IDENTIFIED BY "<REPLACE_WITH_REAL_PASSWORD>";
GRANT CONNECT, RESOURCE TO AIUSER;
ALTER USER AIUSER QUOTA UNLIMITED ON USERS;
BEGIN 
   ORDS.ENABLE_SCHEMA(p_enabled => TRUE, p_schema => 'AIUSER'); 
END;
/

-- Switch to the AIUSER schema
ALTER SESSION SET CURRENT_SCHEMA = AIUSER;

CREATE TABLE collections ( 
    id             VARCHAR2(32) DEFAULT RAWTOHEX(SYS_GUID()) PRIMARY KEY, 
    created_date   TIMESTAMP    DEFAULT SYSTIMESTAMP, 
    modified_date  TIMESTAMP    DEFAULT SYSTIMESTAMP, 
    extra_info     JSON(OBJECT), 
    name           VARCHAR2(500) NOT NULL,
    description    VARCHAR2(500),
    system_name    VARCHAR2(500) UNIQUE NOT NULL,
    source_type    VARCHAR2(50),
    chunk_size     INTEGER
);

CREATE OR REPLACE TRIGGER trg_update_modified_date 
BEFORE UPDATE ON collections 
FOR EACH ROW 
BEGIN 
    :NEW.modified_date := SYSTIMESTAMP; 
END;
/

CREATE TABLE documents ( 
    id             VARCHAR2(32) DEFAULT RAWTOHEX(SYS_GUID()) PRIMARY KEY, 
    created_date   TIMESTAMP    DEFAULT SYSTIMESTAMP, 
    modified_date  TIMESTAMP    DEFAULT SYSTIMESTAMP, 
    collection_id  VARCHAR2(32) NOT NULL, 
    content        CLOB         NOT NULL,
    metadata       JSON,
    extra_info     JSON(OBJECT), 
    embedding      VECTOR       NOT NULL,
    CONSTRAINT fk_collection
        FOREIGN KEY (collection_id) 
        REFERENCES collections(id)
        ON DELETE CASCADE
);

-- Enable full text search on the content column
CREATE SEARCH INDEX idx_document_content_search ON documents(content);

CREATE OR REPLACE TRIGGER trg_doc_update_modified_date 
BEFORE UPDATE ON documents 
FOR EACH ROW 
BEGIN 
    :NEW.modified_date := SYSTIMESTAMP; 
END;
/

CREATE INDEX idx_documents_collection_id ON documents (collection_id);

CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW documents_dv AS
SELECT JSON {
            '_id'           IS d.id,
            'collection_id' IS d.collection_id,
            'content'       IS d.content,
            'metadata'      IS d.metadata,
            d.extra_info AS flex
        }
FROM documents d WITH INSERT UPDATE DELETE;

CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW collections_dv AS
SELECT JSON {
            '_id'          IS c.id,
            'name'         IS c.name,
            'description'  IS c.description,
            'system_name'  IS c.system_name,
            'source_type'  IS c.source_type,
            'chunk_size'   IS c.chunk_size,
            c.extra_info AS flex
        }
FROM collections c WITH INSERT UPDATE DELETE;

EXIT;