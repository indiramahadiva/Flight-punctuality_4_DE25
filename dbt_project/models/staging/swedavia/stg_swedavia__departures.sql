
-- ============================================================
-- Model: stg_swedavia__departures
-- Layer: STAGING
--
-- Purpose:
-- Clean and standardize raw Swedavia departure data
-- before it is used in the fact and dimension models.
--
-- Grain: One row per departure movement.
--
-- Transformations:
-- 1. Rename raw columns to standardized names.
-- 2. Exclude deleted flight records (DEL).
-- 3. Convert the flight departure date to UTC.
-- 4. Calculate departure delays in seconds.
-- 5. Convert scheduled departure time to Swedish calendar date.
-- 6. Preserve ingestion metadata for traceability.
--
-- No joins or aggregations are performed in staging.
-- ============================================================


-- STEP 1: Read and standardize the raw departure data.
with source as (

    select
        -- Preserve the unique key created during ingestion.
        movement_key as raw_movement_key,

        -- Swedavia airport associated with this departure.
        swedavia_airport,

        -- Identify the flight and its departure date.
        flight_leg_identifier__flight_id as flight_id,

        -- Convert to UTC before extracting the date.
        -- The raw column uses TIMESTAMP_LTZ.
        convert_timezone('UTC', flight_leg_identifier__flight_departure_date_utc)::date as departure_date_utc,

        -- IATA airport codes for the flight route.
        flight_leg_identifier__departure_airport_iata as from_iata,
        flight_leg_identifier__arrival_airport_iata as to_iata,

        -- ICAO airport codes for the flight route
        flight_leg_identifier__departure_airport_icao as from_icao,
        flight_leg_identifier__arrival_airport_icao as to_icao,

        -- Airline identifiers and descriptive information.
        airline_operator__icao as airline_icao,
        airline_operator__iata as airline_iata,
        airline_operator__name as airline_name,

        -- Flight status from the Swedavia API.
        location_and_status__flight_leg_status as status,

        -- Scheduled and actual departure timestamps.
        -- Both are stored as TIMESTAMP_LTZ.
        departure_time__scheduled_utc as scheduled_utc,
        departure_time__actual_utc as actual_utc,

        -- dlt metadata for ingestion traceability.
        _dlt_load_id,
        _dlt_id

    -- Read from the raw departures table in Snowflake.
    from {{ source('swedavia', 'departures') }}

    -- Exclude deleted flight records.
    -- Exclude Swedavia test flights (SWD).
    -- Retain cancelled and other statuses for reporting.
    where location_and_status__flight_leg_status != 'DEL'
        and airline_operator__icao != 'SWD'
)


-- STEP 2: Create standardized and calculated columns.
select
    -- Original ingestion key.
    raw_movement_key,

    swedavia_airport,

    -- DEP identifies the movement as a departure.
    'DEP' as direction,

    -- Flight and route identifiers.
    flight_id,
    departure_date_utc,
    from_iata,
    to_iata,
    from_icao,
    to_icao,

    -- Airline information.
    airline_icao,
    airline_iata,
    airline_name,

    -- Flight status and timestamps.
    status,
    scheduled_utc,
    actual_utc,

    -- Calculate departure delay in seconds.
    --
    -- Positive = departed late.
    -- Negative = departed early.
    -- Zero     = departed on schedule.
    -- NULL     = actual departure time is unavailable.
    --
    -- A completed flight is delayed when
    -- delay_seconds > 900 (more than 15 minutes).
    datediff(
        'second',
        scheduled_utc,
        actual_utc
    ) as delay_seconds,

    -- Convert scheduled departure time to Swedish time.
    -- Handles CET/CEST daylight saving automatically.
    --
    -- Extract DATE as the date_key for dim_date.
    convert_timezone(
        'Europe/Stockholm', scheduled_utc)::date as date_key,

    -- Preserve dlt ingestion metadata.
    _dlt_load_id,
    _dlt_id

from source

-- A retimed flight gets a new ingestion key, so the old version stays in raw.
-- Keep only the latest loaded version of each flight leg.
qualify row_number() over (
    partition by flight_id, departure_date_utc, from_iata, to_iata
    order by _dlt_load_id desc, scheduled_utc desc
) = 1
