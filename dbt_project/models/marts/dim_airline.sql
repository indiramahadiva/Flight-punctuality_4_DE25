-- dim_airline
-- One row per airline that has flown at a Swedavia airport.
-- Swedavia decides which airlines exist; Wikipedia only adds the country.
-- Key: airline_icao (natural key, the fact table joins on it).

with swedavia_airlines as (
    select airline_icao, airline_iata, airline_name from {{ ref('stg_swedavia__arrivals') }}
    union all
    select airline_icao, airline_iata, airline_name from {{ ref('stg_swedavia__departures') }}
),

airlines as (
    select
        airline_icao,
        -- Swedavia puts the ICAO code in the IATA field when there's no IATA code (BLX, JON...)
        max(case when length(airline_iata) = 2 then airline_iata end) as airline_iata,
        max(airline_name)                                              as airline_name
    from swedavia_airlines
    where airline_icao is not null
    group by airline_icao
)

select
    a.airline_icao,
    a.airline_iata,
    a.airline_name,
    coalesce(w.airline_country, 'Unknown')    as airline_country
from airlines as a
-- left: no airline disappears if Wikipedia lacks it
left join {{ ref('stg_wikipedia__airlines') }} as w
    on a.airline_icao = w.airline_icao