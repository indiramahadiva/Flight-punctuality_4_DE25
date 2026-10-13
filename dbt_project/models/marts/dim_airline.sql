-- One row per airline seen at a Swedavia airport.
-- Swedavia = the airline list, Wikipedia = just the country.

with swedavia_airlines as (
    select airline_icao, airline_iata, airline_name from {{ ref('stg_swedavia__arrivals') }}
    union all
    select airline_icao, airline_iata, airline_name from {{ ref('stg_swedavia__departures') }}
),

airlines as (
    select
        airline_icao,
        -- no IATA code? Swedavia sticks the ICAO there instead (BLX, JON...), so keep only 2-letter ones
        max(case when length(airline_iata) = 2 then airline_iata end) as airline_iata,
        max(airline_name)                                              as airline_name
    from swedavia_airlines
    where airline_icao is not null
    group by airline_icao
)

select
    {{ dbt_utils.generate_surrogate_key(['a.airline_icao']) }} as airline_id,  -- matches the fact table key
    a.airline_icao,
    a.airline_iata,
    a.airline_name,
    coalesce(w.airline_country, 'Unknown')                     as airline_country
from airlines as a
left join {{ ref('stg_wikipedia__airlines') }} as w            -- left join so we don't lose airlines Wikipedia doesn't have
    on a.airline_icao = w.airline_icao