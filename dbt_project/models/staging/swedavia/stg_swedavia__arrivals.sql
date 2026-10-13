
-- ============================================================
-- Model: stg_swedavia__arrivals
-- Layer: STAGING
--
-- Purpose:
-- Clean and standardize raw Swedavia arrival data
-- before it is used in the fact and dimension models.
--
-- Grain: One row per arrival movement.
--
-- Transformations:
-- 1. Rename raw columns to standardized names.
-- 2. Exclude deleted flight records (DEL).
-- 3. Convert the flight departure date to UTC.
-- 4. Calculate arrival delays in seconds.
-- 5. Convert scheduled arrival time to Swedish calendar date.
-- 6. Preserve ingestion metadata for traceability.
--
-- No joins or aggregations are performed in staging.
-- ============================================================


-- STEP 1: Read and standardize the raw arrival data.
with source as (

    select
        -- Preserve the unique key created during ingestion.
        movement_key as raw_movement_key,

        -- Swedavia airport associated with this arrival.
        swedavia_airport,

        -- Identify the flight and its departure date.
        flight_leg_identifier__flight_id as flight_id,

        -- Convert the source timestamp to UTC before extracting the departure calendar date.
        convert_timezone(
            'UTC', flight_leg_identifier__flight_departure_date_utc)::date as departure_date_utc,

        -- IATA airport codes for the flight route
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

        -- Scheduled and actual arrival timestamps.
        -- These timestamps are stored as TIMESTAMP_LTZ.
        arrival_time__scheduled_utc as scheduled_utc,
        arrival_time__actual_utc as actual_utc,

        -- dlt metadata for tracking ingestion and lineage.
        _dlt_load_id,
        _dlt_id

    -- dbt source() references the raw Snowflake table
    -- declared in the project's sources YAML file.
    from {{ source('swedavia', 'arrivals') }}

    -- Exclude DEL (deleted) records.
    -- Keep cancelled (CAN) and other flight statuses
    -- for downstream reporting and analysis.
    where location_and_status__flight_leg_status != 'DEL'
        and airline_operator__icao != 'SWD'

)


-- STEP 2: Create standardized and calculated columns.
select
    -- Preserve the original ingestion identifier.
    raw_movement_key,

    swedavia_airport,

    -- ARR identifies this record as an arrival.
    -- Departures will use DEP in their staging model.
    'ARR' as direction,

    -- Standardized flight and route information.
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

    -- Calculate the difference between actual
    -- and scheduled arrival times in seconds.
    --
    -- Positive = arrived late.
    -- Negative = arrived early.
    -- Zero     = arrived exactly on schedule.
    -- NULL     = actual arrival time is unavailable.
    --
    -- Business rule:
    -- A completed flight is delayed if delay_seconds > 900.
    datediff(
        'second',
        scheduled_utc,
        actual_utc
    ) as delay_seconds,

    -- Convert the scheduled arrival timestamp to
    -- the Europe/Stockholm timezone.
    --
    -- This handles daylight saving time automatically.
    -- Extract DATE to create the date_key used by dim_date.
    convert_timezone(
        'Europe/Stockholm', scheduled_utc)::date as date_key,

    -- Preserve dlt metadata for troubleshooting.
    _dlt_load_id,
    _dlt_id

from source
