# EDA findings: Swedavia FlightInfo

# EDA findings: Swedavia FlightInfo

Findings that decide the dimensional model, one question at a time. Every number comes from a query in `notebooks/eda_swedavia.ipynb`.

**Source:** `data/sandbox_swedavia_merge.duckdb`, schema `swedavia_raw`, loaded by dlt with merge (not in git, `data/` is ignored).
**Scope:** 10 Swedavia airports, both directions, Swedish days 5–8 October 2026. Last load 8 Oct 12:01 UTC.

## 1. Shape: what is in the data?

- `arrivals` 2 121 rows, `departures` 2 111 rows.
- Scheduled times cover four full Swedish days: 5 Oct 00:00 to 8 Oct 23:55 (+02:00).
- The Swedavia airport is in a different column per direction: `arrival_airport_iata` for arrivals, `departure_airport_iata` for departures.
- Volume per airport is stable day to day: ARN about 350 per direction, KRN 2.

**For the model:** staging gives both directions the same column names, with one column for the Swedavia airport.

## 2. Identity: what identifies one flight?

- Candidate key: `direction` + `flight_id` + `departure_date_utc` + `from_iata` + `to_iata`.
- All rows: 2 duplicates, both arrivals (`BLX496` RHO -> GOT, `D84528` RAK -> ARN). Each is one `DEL` row plus one `LAN` row from the same load, so the API sends both.
- Without `DEL`: 0 duplicates in both directions (1 769 arrivals, 1 758 departures).

**For the model:** grain = one flight leg at a Swedavia airport, per direction. `DEL` is filtered in staging, and a `unique` test guards the key after the filter.

## 3. Status: which rows count?

| Status | Meaning | Arrivals | Departures | With actual time |
|---|---|---|---|---|
| `LAN` / `ACT` | Landed / Departed | 1 486 (70.1 %) | 1 497 (70.9 %) | all |
| `DEL` | Deleted | 352 (16.6 %) | 353 (16.7 %) | 1 departure |
| `SCH` | Scheduled | 267 (12.6 %) | 189 (9.0 %) | 0 |
| `SEQ` | Sequenced | – | 53 (2.5 %) | 0 |
| `CAN` | Cancelled | 16 (0.8 %) | 19 (0.9 %) | 1 departure |

- `DEL` and `CAN` are different codes in the API spec: a deleted record is not a cancelled flight.
- `SCH` and `SEQ` appear only on the load day: flights that had not happened yet. Exception: 5 departures on 5 Oct are still `SCH`.

**For the model:** delay is measured on `LAN` / `ACT` only. `CAN` is its own measure. `SCH` / `SEQ` are not counted. Delayed = more than 15 minutes (`delay_seconds > 900`), agreed by the group 8 Oct.

## 4. Delay: which time fields, and the distribution around 900 s
*Open*

## 5. Codeshare: one flight with several flight numbers
*Open*

## 6. Domestic flights: in both tables
*Open*

## 7. Date: which day does the fact carry?
*Open*

## 8. Keys against Wikipedia: IATA or ICAO?
*Open*

## Not investigated yet

- About 34 `DEL` rows per direction have a live row with another flight number, same route and same time. Possibly codeshare (question 5).
- 5 departures on 5 Oct still `SCH` two days later: warn, or filter silently?