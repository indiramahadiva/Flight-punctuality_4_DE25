-- 04: Rights along the chain. Run as SECURITYADMIN (the guard).
USE ROLE SECURITYADMIN;

-- All three roles may use the warehouse and the database
GRANT USAGE ON WAREHOUSE flights_wh TO ROLE flights_loader;
GRANT USAGE ON WAREHOUSE flights_wh TO ROLE flights_transformer;
GRANT USAGE ON WAREHOUSE flights_wh TO ROLE flights_reporter;

GRANT USAGE ON DATABASE flights_db TO ROLE flights_loader;
GRANT USAGE ON DATABASE flights_db TO ROLE flights_transformer;
GRANT USAGE ON DATABASE flights_db TO ROLE flights_reporter;

-- dlt creates its own staging schema for merges, and dbt its dbt_<name> schemas
GRANT CREATE SCHEMA ON DATABASE flights_db TO ROLE flights_loader;
GRANT CREATE SCHEMA ON DATABASE flights_db TO ROLE flights_transformer;

-- dbt reads the raw data
GRANT USAGE ON SCHEMA flights_db.swedavia_raw TO ROLE flights_transformer;
GRANT SELECT ON ALL TABLES    IN SCHEMA flights_db.swedavia_raw TO ROLE flights_transformer;
GRANT SELECT ON FUTURE TABLES IN SCHEMA flights_db.swedavia_raw TO ROLE flights_transformer;
GRANT SELECT ON ALL VIEWS     IN SCHEMA flights_db.swedavia_raw TO ROLE flights_transformer;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA flights_db.swedavia_raw TO ROLE flights_transformer;

GRANT USAGE ON SCHEMA flights_db.wikipedia_raw TO ROLE flights_transformer;
GRANT SELECT ON ALL TABLES    IN SCHEMA flights_db.wikipedia_raw TO ROLE flights_transformer;
GRANT SELECT ON FUTURE TABLES IN SCHEMA flights_db.wikipedia_raw TO ROLE flights_transformer;
GRANT SELECT ON ALL VIEWS     IN SCHEMA flights_db.wikipedia_raw TO ROLE flights_transformer;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA flights_db.wikipedia_raw TO ROLE flights_transformer;

-- Streamlit reads marts, nothing else
GRANT USAGE ON SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON ALL TABLES    IN SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON FUTURE TABLES IN SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON ALL VIEWS     IN SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA flights_db.marts TO ROLE flights_reporter;