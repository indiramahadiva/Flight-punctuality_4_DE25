-- Swedavia runs exactly TEN airports.
-- Returns one row when the count is anything else.
{{ config(severity='warn') }}

select count(*) as swedavia_airports
from {{ ref('dim_airport') }}
where is_swedavia
having count(*) != 10