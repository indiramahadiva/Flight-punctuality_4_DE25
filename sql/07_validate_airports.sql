-- Validate all 10 airports, movement keys, and both tables


-- =====================================================
-- TEST 1: RAW DATA COMPLETENESS AND UNIQUENESS
-- =====================================================
-- Verify both resources have records from all 10 airports.
-- Check that flight movements have unique, non-NULL keys.

WITH all_movements AS (

    SELECT
        'arrivals' AS movement_type,
        swedavia_airport,
        movement_key
    FROM flights_db.swedavia_raw.arrivals

    UNION ALL

    SELECT
        'departures' AS movement_type,
        swedavia_airport,
        movement_key
    FROM flights_db.swedavia_raw.departures
)

SELECT
    movement_type,

    COUNT(*) AS total_rows,
    -- How many flight records were loaded?

    COUNT(DISTINCT swedavia_airport) AS total_airports,
    -- How many different airports appear?

    COUNT(DISTINCT movement_key) AS unique_movements,
    -- How many distinct flight movements exist?

    SUM(IFF(movement_key IS NULL, 1, 0)) AS null_keys
    -- How many records have missing movement keys?

FROM all_movements
GROUP BY movement_type
ORDER BY movement_type;





-- =====================================================
-- TEST 2: INSPECT SCHEDULED FLIGHT DATE COVERAGE
-- =====================================================
-- Group arrivals by their scheduled UTC calendar date.
-- This helps identify missing or unexpected flight dates.

SELECT
    TO_DATE(arrival_time__scheduled_utc) AS flight_date,
    COUNT(*) AS total_arrivals,
    COUNT(DISTINCT swedavia_airport) AS airports_with_arrivals

FROM flights_db.swedavia_raw.arrivals

GROUP BY flight_date
ORDER BY flight_date DESC;




-- =====================================================
-- TEST 3: CHECK FOR DUPLICATES AFTER REPEATED INGESTION
-- =====================================================
-- If a movement_key appears more than once, the raw table
-- contains duplicate records for that flight movement.

SELECT
    movement_key,
    COUNT(*) AS occurrences

FROM flights_db.swedavia_raw.arrivals

GROUP BY movement_key
HAVING COUNT(*) > 1;






-- Group flights by Swedish local calendar date instead of UTC.
-- Assumes scheduled_utc is stored as a UTC timestamp.

SELECT
    TO_DATE(
        CONVERT_TIMEZONE(
            'UTC',
            'Europe/Stockholm',
            arrival_time__scheduled_utc::TIMESTAMP_NTZ
        )
    ) AS swedish_flight_date,

    COUNT(*) AS total_arrivals,

    COUNT(DISTINCT swedavia_airport) AS airports

FROM flights_db.swedavia_raw.arrivals

GROUP BY swedish_flight_date
ORDER BY swedish_flight_date DESC;





-- Investigate flight records outside our 3-day extraction window.
-- We requested October 7, 8, and 9.
-- But 23 arrivals are still dated October 6.

SELECT
    swedavia_airport,
    flight_id,
    arrival_time__scheduled_utc,
    movement_key

FROM flights_db.swedavia_raw.arrivals

WHERE TO_DATE(
    CONVERT_TIMEZONE(
        'UTC',
        'Europe/Stockholm',
        arrival_time__scheduled_utc::TIMESTAMP_NTZ
    )
) = '2026-10-06'

ORDER BY swedavia_airport, arrival_time__scheduled_utc;



-- Base check after rerunning dlt pipeline
SELECT
    'arrivals' AS movement_type,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT movement_key) AS unique_movements
FROM flights_db.swedavia_raw.arrivals

UNION ALL

SELECT
    'departures' AS movement_type,
    COUNT(*) AS total_rows,
    COUNT(DISTINCT movement_key) AS unique_movements
FROM flights_db.swedavia_raw.departures;