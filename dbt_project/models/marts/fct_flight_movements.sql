-- One row per arrival or departure at a Swedavia airport.

with movements as (

    -- Get arrivals and identify the departure airport as the other airport.
    select
        direction,
        flight_id,
        departure_date_utc,
        from_iata,
        to_iata,
        airline_icao,
        swedavia_airport,
        from_iata as other_airport_iata,
        date_key,
        status,
        scheduled_utc,
        actual_utc,
        delay_seconds
    from {{ ref('stg_swedavia__arrivals') }}

    union all -- Combine arrivals and departures, keeping all rows.

    -- Get departures and identify the arrival airport as the other airport.
    select
        direction,
        flight_id,
        departure_date_utc,
        from_iata,
        to_iata,
        airline_icao,
        swedavia_airport,
        to_iata as other_airport_iata,
        date_key,
        status,
        scheduled_utc,
        actual_utc,
        delay_seconds
    from {{ ref('stg_swedavia__departures') }}
)

select
    -- Unique identifier for each flight movement.
    {{ dbt_utils.generate_surrogate_key([
        'direction',
        'flight_id',
        'departure_date_utc',
        'from_iata',
        'to_iata'
    ]) }} as movement_id,

    date_key,

    -- Generate keys to link the fact table to dimensions.
    {{ dbt_utils.generate_surrogate_key([
        'airline_icao'
    ]) }} as airline_id,

    {{ dbt_utils.generate_surrogate_key([
        'swedavia_airport'
    ]) }} as swedavia_airport_id,

    {{ dbt_utils.generate_surrogate_key([
        'other_airport_iata'
    ]) }} as other_airport_id,

    -- Flight details and delay information.
    direction,
    flight_id,
    status,
    scheduled_utc,
    actual_utc,
    delay_seconds

from movements