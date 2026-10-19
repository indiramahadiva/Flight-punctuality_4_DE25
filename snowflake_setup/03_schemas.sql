-- 03: Schemas up front, then ownership to the right role. Run as SYSADMIN (the builder).
USE ROLE SYSADMIN;

CREATE SCHEMA IF NOT EXISTS flights_db.swedavia_raw;
CREATE SCHEMA IF NOT EXISTS flights_db.wikipedia_raw;
CREATE SCHEMA IF NOT EXISTS flights_db.staging;
CREATE SCHEMA IF NOT EXISTS flights_db.marts;

-- The raw data is owned by dlt
GRANT OWNERSHIP ON SCHEMA flights_db.swedavia_raw  TO ROLE flights_loader;
GRANT OWNERSHIP ON SCHEMA flights_db.wikipedia_raw TO ROLE flights_loader;

-- What dbt builds is owned by dbt
GRANT OWNERSHIP ON SCHEMA flights_db.staging TO ROLE flights_transformer;
GRANT OWNERSHIP ON SCHEMA flights_db.marts   TO ROLE flights_transformer;