-- dbt_project/macros/generate_schema_name.sql
-- Chooses schema per model
-- DAGSTER (DBT_TARGET=PROD): staging and marts 
-- DEV(Development): dbt_<NAME>_marts
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if target.name == 'prod' and custom_schema_name is not none -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ default__generate_schema_name(custom_schema_name, node) }}
    {%- endif -%}
{%- endmacro %}