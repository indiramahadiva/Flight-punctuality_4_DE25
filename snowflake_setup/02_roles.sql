-- 02: Roller, en per verktyg. Körs som USERADMIN (receptionen).
USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS flights_loader;      -- dlt
CREATE ROLE IF NOT EXISTS flights_transformer; -- dbt
CREATE ROLE IF NOT EXISTS flights_reporter;    -- Streamlit

-- Rollerna under SYSADMIN, så att byggaren kan förvalta det de skapar
GRANT ROLE flights_loader      TO ROLE SYSADMIN;
GRANT ROLE flights_transformer TO ROLE SYSADMIN;
GRANT ROLE flights_reporter    TO ROLE SYSADMIN;