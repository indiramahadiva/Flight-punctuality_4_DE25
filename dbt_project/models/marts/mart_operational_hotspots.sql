-- mart_operational_hotspots
-- One row per date, Swedavia airport, scheduled hour (Swedish time) and direction.
-- Feeds the Operational Delay Impact & Hotspots page: heatmap, traffic vs delay rate,
-- delay severity and accumulated delay time.
-- Delayed = completed (LAN/ACT) and more than 15 minutes (900 seconds) late.

with movements as (
    select
        f.date_key,
        f.swedavia_airport_iata,
        ap.airport_name                                             as swedavia_airport_name,
        -- same conversion as date_key in staging, so hour and date always match
        hour(convert_timezone('Europe/Stockholm', f.scheduled_utc)) as scheduled_hour,
        f.direction,
        f.status in ('LAN', 'ACT')                                  as is_completed,
        f.status = 'CAN'                                            as is_cancelled,
        f.delay_seconds
    from {{ ref('fct_flight_movements') }} as f
    join {{ ref('dim_airport') }} as ap
        on f.swedavia_airport_iata = ap.airport_iata
),

flagged as (
    select
        *,
        is_completed and delay_seconds > 900                        as is_delayed
    from movements
)

select
    date_key,
    swedavia_airport_iata,
    swedavia_airport_name,
    scheduled_hour,
    direction,

    -- traffic and punctuality
    count(*)                                                        as movements,
    count_if(is_completed)                                          as completed,
    count_if(is_delayed)                                            as delayed,
    count_if(is_cancelled)                                          as cancelled,

    -- severity: delayed flights by duration
    count_if(is_delayed and delay_seconds <= 1800)                  as delayed_15_30,
    count_if(is_delayed and delay_seconds > 1800 and delay_seconds <= 3600) as delayed_30_60,
    count_if(is_delayed and delay_seconds > 3600)                   as delayed_60_plus,

    -- accumulated delay time for flights more than 15 minutes late
    sum(iff(is_delayed, delay_seconds, 0)) / 60                     as delay_minutes,

    div0(delayed, completed)                                        as delayed_share
from flagged
group by all