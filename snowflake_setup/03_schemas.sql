-- 03: Scheman i förväg, sedan ägarskap till rätt roll. Körs som SYSADMIN (byggaren).
USE ROLE SYSADMIN;

CREATE SCHEMA IF NOT EXISTS flights_db.swedavia_raw;
CREATE SCHEMA IF NOT EXISTS flights_db.wikipedia_raw;
CREATE SCHEMA IF NOT EXISTS flights_db.staging;
CREATE SCHEMA IF NOT EXISTS flights_db.marts;

-- Rådatan ägs av dlt
GRANT OWNERSHIP ON SCHEMA flights_db.swedavia_raw  TO ROLE flights_loader;
GRANT OWNERSHIP ON SCHEMA flights_db.wikipedia_raw TO ROLE flights_loader;

-- Det dbt bygger ägs av dbt
GRANT OWNERSHIP ON SCHEMA flights_db.staging TO ROLE flights_transformer;
GRANT OWNERSHIP ON SCHEMA flights_db.marts   TO ROLE flights_transformer;