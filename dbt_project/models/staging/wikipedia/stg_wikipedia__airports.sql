-- One row per airport IATA code. Cleans Wikipedia's quirks, no joins.

with source as (
    select * from {{ source('wikipedia', 'airports') }}
),

cleaned as (
    select
        regexp_replace(iata_code, '\\[[0-9]+\\]', '') as iata_codes,  -- strip footnotes like [2]
        trim(airport)  as airport_name,
        trim(location) as city,
        trim(country)  as country
    from source
    where iata_code is not null                                      -- drop the empty row
),

split_codes as (
    select
        trim(f.value::string) as airport_iata,                      -- BSL/MLH/EAP -> 3 rows
        c.airport_name,
        c.city,
        c.country
    from cleaned as c,
        lateral flatten(input => split(c.iata_codes, '/')) as f
)

select *
from split_codes
-- one row per code (Basel x3 -> France, Uruapan x2 -> 1)
qualify row_number() over (partition by airport_iata order by country) = 1