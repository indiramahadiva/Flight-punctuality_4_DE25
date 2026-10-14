-- mart_delays_daily
-- One row per date, Swedavia airport, airline and direction.
-- The dashboard reads this table and only sums the numbers.
-- Delayed = completed and more than 15 minutes (900 seconds) late.
-- Completed = LAN for arrivals, ACT for departures.

with movements as (
    select
        f.date_key,
        f.swedavia_airport_iata,
        ap.airport_name                                     as swedavia_airport_name,
        f.airline_icao,
        al.airline_name,
        f.direction,
        f.status,
        f.delay_seconds
    from {{ ref('fct_flight_movements') }} as f
    join {{ ref('dim_airport') }} as ap
        on f.swedavia_airport_iata = ap.airport_iata
    join {{ ref('dim_airline') }} as al
        on f.airline_icao = al.airline_icao
)

select
    date_key,
    swedavia_airport_iata,
    swedavia_airport_name,
    airline_icao,
    airline_name,
    direction,
    count(*)                                                as movements,
    count_if(status in ('LAN', 'ACT'))                      as completed,
    count_if(status in ('LAN', 'ACT') and delay_seconds > 900) as delayed,
    count_if(status = 'CAN')                                as cancelled,
    div0(delayed, completed)                                as delayed_share
from movements
group by all