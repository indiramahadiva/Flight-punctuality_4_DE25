-- mart_operational_hotspots (per hour) and mart_delays_daily (per airline) count
-- the same flights with the same delay rule. Summed up to the level they share,
-- date x Swedavia airport x direction, they must give the same totals.
-- Returns the rows where they differ; zero rows = pass.
--
-- Catches e.g. a changed delay rule in one mart only, a missing DEL/SWD filter,
-- or the hour and date computed in different time zones.

with hotspots as (
    select
        date_key,
        swedavia_airport_iata,
        direction,
        sum(movements)  as movements,
        sum(completed)  as completed,
        sum(delayed)    as delayed,
        sum(cancelled)  as cancelled
    from {{ ref('mart_operational_hotspots') }}
    group by all
),

daily as (
    select
        date_key,
        swedavia_airport_iata,
        direction,
        sum(movements)  as movements,
        sum(completed)  as completed,
        sum(delayed)    as delayed,
        sum(cancelled)  as cancelled
    from {{ ref('mart_delays_daily') }}
    group by all
)

select
    date_key,
    swedavia_airport_iata,
    direction,
    h.movements as hotspots_movements,  d.movements as daily_movements,
    h.completed as hotspots_completed,  d.completed as daily_completed,
    h.delayed   as hotspots_delayed,    d.delayed   as daily_delayed,
    h.cancelled as hotspots_cancelled,  d.cancelled as daily_cancelled
from hotspots as h
full outer join daily as d
    using (date_key, swedavia_airport_iata, direction)
where h.movements is distinct from d.movements
   or h.completed is distinct from d.completed
   or h.delayed   is distinct from d.delayed
   or h.cancelled is distinct from d.cancelled
