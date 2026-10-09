-- Validate DLT Layer


SELECT *
FROM flights_db.swedavia_raw.arrivals
LIMIT 10;

SELECT *
FROM flights_db.swedavia_raw.departures
LIMIT 10;





-- ============================================================
-- QUERY 2: Count flights per airport
-- ============================================================
/* 
Validates that the dlt pipeline has ingested flight records for all 10 Swedish airports 
and lets us compare the number of arrivals and departures.
-- UNION ALL keeps every result row from both queries.
-- Unlike UNION, it does not remove duplicate result rows.
*/
SELECT
    'arrivals' AS movement_type,
    swedavia_airport,
    COUNT(*) AS total_flights
FROM flights_db.swedavia_raw.arrivals
GROUP BY swedavia_airport

UNION ALL

SELECT
    'departures' AS movement_type,
    swedavia_airport,
    COUNT(*) AS total_flights
FROM flights_db.swedavia_raw.departures
GROUP BY swedavia_airport

ORDER BY swedavia_airport, movement_type;




-- ============================================================
-- QUERY 3: VALIDATE FLIGHT MOVEMENT KEYS ARRIVALS
-- ============================================================
-- Purpose:
-- Check whether every arrival record has a unique movement
-- key and whether any movement keys are missing (NULL).
--
-- In swedavia.py, we created movement_key by combining:
-- airport + direction + flight_id + scheduled_utc
--
-- Example:
-- ARN|arrival|SK123|2026-10-09T10:00:00Z
--
-- Our dlt resource uses:
-- write_disposition="merge"
-- primary_key="movement_key"
--
-- This tells dlt to use movement_key when matching incoming
-- flight records against records already in Snowflake.
--
-- The goal is to update existing flight movements rather
-- than insert duplicates during repeated ingestion.
-- ============================================================

/*
Verify movement keys
checks whether the arrivals table contains duplicate or missing movement_key values.
*/
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT movement_key) AS unique_movements
FROM flights_db.swedavia_raw.arrivals;


-- ============================================================
-- QUERY 4: VALIDATE FLIGHT MOVEMENT KEYS DEPARTURES
-- ============================================================
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT movement_key) AS unique_movements
FROM flights_db.swedavia_raw.departures;

