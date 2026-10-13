-- dim_airport
-- One row per airport that appears in Swedavia's flights, at either end.
-- Swedavia decides which airports exist.
-- The seed adds name, city and country for Swedish airports, plus the is_swedavia flag.
-- Wikipedia adds name, city and country for everything else.
-- Key: airport_iata (natural key, the fact table joins on it).

with swedavia_codes as (
    -- every airport code in the flights, both ends, both directions
    -- union (not union all) removes duplicates, so each code appears once
    select from_iata as airport_iata from {{ ref('stg_swedavia__arrivals') }}
    union
    select to_iata   from {{ ref('stg_swedavia__arrivals') }}
    union
    select from_iata from {{ ref('stg_swedavia__departures') }}
    union
    select to_iata   from {{ ref('stg_swedavia__departures') }}
)

select
    c.airport_iata,

    -- the seed wins for Swedish airports, Wikipedia fills in the rest,
    -- 'Unknown' when neither has the airport
    coalesce(s.airport_name, w.airport_name, 'Unknown')    as airport_name,
    coalesce(s.city, w.city, 'Unknown')                    as city,
    case
        when s.iata_code is not null then 'Sweden'          -- every seed row is Swedish
        else coalesce(w.country, 'Unknown')
    end                                                     as country,

    -- true only for Swedavia's ten airports
    coalesce(s.is_swedavia, false)                          as is_swedavia

from swedavia_codes as c
-- left joins: no airport disappears if the seed or Wikipedia lacks it
left join {{ ref('swedavia_airports') }} as s
    on c.airport_iata = s.iata_code
left join {{ ref('stg_wikipedia__airports') }} as w
    on c.airport_iata = w.airport_iata

where c.airport_iata is not null