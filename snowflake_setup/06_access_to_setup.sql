-- Ran this to get access to roles created.

USE ROLE flights_loader;

USE SECONDARY ROLES NONE;

USE WAREHOUSE flights_wh;

SHOW SCHEMAS IN DATABASE flights_db;

SHOW GRANTS TO ROLE flights_loader;