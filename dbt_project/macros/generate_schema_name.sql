-- dbt_project/macros/generate_schema_name.sql
-- Väljer schema per modell
-- DAGSTER (DBT_TARGET=PROD): staging och marts rakt av
-- UTVECKLING: dbt_<NAMN>_marts
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if target.name == 'prod' and custom_schema_name is not none -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ default__generate_schema_name(custom_schema_name, node) }}
    {%- endif -%}
{%- endmacro %}