
-- One row per date, airport, airline, scheduled hour and direction.
-- Supports the Airline Delay Hotspots heatmap.

with movements as (
    select
        f.date_key,
        f.swedavia_airport_iata,
        ap.airport_name as swedavia_airport_name,
        f.airline_icao,
        coalesce(al.airline_name, f.airline_icao, 'Unknown airline') as airline_name,
        hour(convert_timezone('Europe/Stockholm', f.scheduled_utc)) as scheduled_hour,
        f.direction,
        f.status,
        f.delay_seconds

    from {{ ref('fct_flight_movements') }} as f

    left join {{ ref('dim_airline') }} as al
        on f.airline_icao = al.airline_icao

    left join {{ ref('dim_airport') }} as ap
        on f.swedavia_airport_iata = ap.airport_iata
),

counts as (
    select
        date_key,
        swedavia_airport_iata,
        swedavia_airport_name,
        airline_icao,
        airline_name,
        scheduled_hour,
        direction,

        count(*) as movements,

        coalesce(count_if(status in ('LAN', 'ACT')), 0) as completed,

        coalesce(count_if(
            status in ('LAN', 'ACT') and delay_seconds > 900
        ), 0) as delayed,

        coalesce(count_if(status = 'CAN'), 0) as cancelled

    from movements
    group by all
)

select
    *,
    delayed / nullif(completed, 0) as delayed_share

from counts
