-- 04: Rättigheter enligt kedjan. Körs som SECURITYADMIN (vakten).
USE ROLE SECURITYADMIN;

-- Alla tre rollerna får använda warehouse och databas
GRANT USAGE ON WAREHOUSE flights_wh TO ROLE flights_loader;
GRANT USAGE ON WAREHOUSE flights_wh TO ROLE flights_transformer;
GRANT USAGE ON WAREHOUSE flights_wh TO ROLE flights_reporter;

GRANT USAGE ON DATABASE flights_db TO ROLE flights_loader;
GRANT USAGE ON DATABASE flights_db TO ROLE flights_transformer;
GRANT USAGE ON DATABASE flights_db TO ROLE flights_reporter;

-- dlt skapar sitt mellanlager och dbt sina dbt_<namn>-scheman
GRANT CREATE SCHEMA ON DATABASE flights_db TO ROLE flights_loader;
GRANT CREATE SCHEMA ON DATABASE flights_db TO ROLE flights_transformer;

-- dbt läser rådatan
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

-- Streamlit läser marts, inget annat
GRANT USAGE ON SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON ALL TABLES    IN SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON FUTURE TABLES IN SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON ALL VIEWS     IN SCHEMA flights_db.marts TO ROLE flights_reporter;
GRANT SELECT ON FUTURE VIEWS  IN SCHEMA flights_db.marts TO ROLE flights_reporter;