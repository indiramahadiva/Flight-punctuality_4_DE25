-- 05: One user per tool, each with its own role. Run as USERADMIN, then SECURITYADMIN.
-- Replace the three password placeholders in your Snowflake worksheet, never in this file.
-- Use the same passwords in .env.
-- In an account that already has these users, this resets their passwords.
USE ROLE USERADMIN;

CREATE USER IF NOT EXISTS dlt_user       DEFAULT_ROLE = flights_loader      DEFAULT_WAREHOUSE = flights_wh;
CREATE USER IF NOT EXISTS dbt_user       DEFAULT_ROLE = flights_transformer DEFAULT_WAREHOUSE = flights_wh;
CREATE USER IF NOT EXISTS streamlit_user DEFAULT_ROLE = flights_reporter    DEFAULT_WAREHOUSE = flights_wh;

-- ALTER sets the password on every run. CREATE USER IF NOT EXISTS would skip an existing user silently.
ALTER USER dlt_user       SET PASSWORD = '<dlt_password>';
ALTER USER dbt_user       SET PASSWORD = '<dbt_password>';
ALTER USER streamlit_user SET PASSWORD = '<streamlit_password>';

USE ROLE SECURITYADMIN;

GRANT ROLE flights_loader      TO USER dlt_user;
GRANT ROLE flights_transformer TO USER dbt_user;
GRANT ROLE flights_reporter    TO USER streamlit_user;
