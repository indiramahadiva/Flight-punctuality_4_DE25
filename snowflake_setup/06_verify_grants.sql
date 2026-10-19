-- 06: Prove the setup, one role at a time, then the users. NO borrowed roles.
-- Run all stops with an error if a role cannot use the warehouse OR the database.
-- Select one block and press Ctrl+Enter to read its results.

-- Streamlit: Should see marts and nothing else.
USE ROLE flights_reporter;
USE SECONDARY ROLES NONE;
USE WAREHOUSE flights_wh;

SHOW SCHEMAS IN DATABASE flights_db;
SHOW GRANTS TO ROLE flights_reporter;

-- dbt: SHould see the RAW data (read) plus staging and marts (own)
USE ROLE flights_transformer;
USE SECONDARY ROLES NONE;
USE WAREHOUSE flights_wh;

SHOW SCHEMAS IN DATABASE flights_db;
SHOW GRANTS TO ROLE flights_transformer;

-- dlt: Should only see the RAW data which it owns
USE ROLE flights_loader;
USE SECONDARY ROLES NONE;
USE WAREHOUSE flights_wh;

SHOW SCHEMAS IN DATABASE flights_db;
SHOW GRANTS TO ROLE flights_loader;

-- Users: Each should hold exactly one flights_ role
USE ROLE SECURITYADMIN;

SHOW GRANTS TO USER dlt_user;
SHOW GRANTS TO USER dbt_user;
SHOW GRANTS TO USER streamlit_user;