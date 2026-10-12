-- One row per airline ICAO code. Cleans codes, flags defunct airlines,
-- and picks one airline when Wikipedia lists several under the same ICAO.

with source as (
    select * from {{ source('wikipedia', 'airlines') }}
),

cleaned as (
    select
        trim(regexp_replace(icao, '\\[[0-9]+\\]', ''))                       as airline_icao,
        nullif(trim(replace(regexp_replace(iata, '\\[[0-9]+\\]', ''), '*', '')), '') as airline_iata,
        trim(airline)                                                        as airline_name,
        trim(country_region)                                                 as airline_country,
        coalesce(comments ilike any (
            '%defunct%', '%ceased%', '%merged%', '%no longer%',
            '%revoked%', '%bankrupt%', '%changed from%'
        ), false)                                                            as is_defunct
    from source
    where icao is not null
)

select *
from cleaned
-- one row per ICAO: active airlines first, then ones with an IATA code
qualify row_number() over (
    partition by airline_icao
    order by is_defunct, airline_iata nulls last, airline_name
) = 1