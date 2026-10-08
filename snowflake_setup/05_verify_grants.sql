-- 05: Bevisa rättigheterna, en roll i taget. Inga lånade roller.
USE ROLE flights_reporter;
USE SECONDARY ROLES NONE;
USE WAREHOUSE flights_wh;

SHOW SCHEMAS IN DATABASE flights_db;


-- dbt: ska se rådatan (läsa) samt staging och marts (äga)
USE ROLE flights_transformer;
USE SECONDARY ROLES NONE;
USE WAREHOUSE flights_wh;

SHOW SCHEMAS IN DATABASE flights_db;


-- dlt: ska bara se rådatan, som den äger
USE ROLE flights_loader;
USE SECONDARY ROLES NONE;
USE WAREHOUSE flights_wh;

SHOW SCHEMAS IN DATABASE flights_db;