-- 02: Roles, one per tool. Run as USERADMIN (the front desk).
USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS flights_loader;      -- dlt
CREATE ROLE IF NOT EXISTS flights_transformer; -- dbt
CREATE ROLE IF NOT EXISTS flights_reporter;    -- Streamlit

-- The roles go under SYSADMIN, so the builder can manage what they create
GRANT ROLE flights_loader      TO ROLE SYSADMIN;
GRANT ROLE flights_transformer TO ROLE SYSADMIN;
GRANT ROLE flights_reporter    TO ROLE SYSADMIN;