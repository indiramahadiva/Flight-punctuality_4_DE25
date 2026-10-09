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
- Both directions have `scheduled_utc`, `estimated_utc` and `actual_utc`. Delay = `actual_utc` - `scheduled_utc` in seconds, on `LAN` / `ACT` only.
- Scheduled times are always in *whole minutes*. Actual times often have seconds.

| | Arrivals | Departures |
|---|---|---|
| Completed flights | 1 486 | 1 497 |
| Early (< 0 s) | 1 073 | 765 |
| Median | -480 s | -16 s |
| 90th percentile | 840 s | 1 203 s |
| Max | 12 390 s | 11 605 s |
| **Delayed (> 900 s)** | **141 (9.5 %)** | **194 (13.0 %)** |
| `>= 900 s` | 146 | 194 |
| `date_diff('minute') > 15` | 139 | 189 |

- Negative = early. Most arrivals land early because airlines pad the scheduled arrival time. The earliest are long-haul flights (JFK, EWR, HND, PEK).
- 5 arrivals were exactly 900 s late. "More than 15 minutes" leaves them out.
- `date_diff('minute')` counts minute boundaries, not elapsed time: 15 min 40 s becomes 15. It misses 2 arrivals and 5 departures.

**For the model this indicates that:** the fact stores `delay_seconds` with sign (negative = early), computed in seconds, not with `date_diff('minute')`. Delayed = `delay_seconds > 900`. An average delay is pulled down by early arrivals; the share delayed is not.

## 5. Codeshare: one flight with several flight numbers
- Codeshare = one physical flight sold under several flight numbers. Example: `LH814` FRA -> GOT, operated by Lufthansa, also sold under 8 partner numbers (AC, ET, EY, NH, OS, SN, SQ, UA).
- Swedavia sends the partner numbers as a list inside the flight. dlt puts the list in a child table, `<table>__code_share_data`, linked by `_dlt_parent_id` -> `_dlt_id`.
- About **40%** of flights have `codeshare`: 723 of 1 769 arrivals, 699 of 1 758 departures. *Max 8* partner numbers per arrival, 9 per departure.
- No partner number appears as its own row on the same flight leg: 0 in both directions. `One row = one physical flight`.
- The 34 `DEL` rows per direction with a live twin under another number are not `codeshare`. Swedavia corrected the flight number or the operator by deleting and recreating the row (`FRO670` -> `FT670`, `LH800` -> `VL800`). The `DEL` filter removes them.

**For the model this indicates that:** we should count rows, not flight numbers. The `codeshare` table is never joined into the fact, since one row per partner number would multiply the flight and its delay.

## 6. Domestic flights: in both tables
- A flight between two Swedavia airports is a departure at one and an arrival at the other, so it is in both tables with the same key.
- 503 flights are in both tables: about **29%** of each direction (1 758 departures, 1 769 arrivals). Most are **SAS**.
- The two rows are two different events. Of 412 flights completed at both ends: 24 delayed at departure, 22 at arrival. 6 late departures caught up in the air, and 4 flights were late only on arrival.
- 7 rows have **no twin**: flights that departed 4 Oct (outside the window), and two flights that returned to Arlanda (`ARN` -> `ARN`).

**For the model this means:** keep both rows, since they are two movements with two delays. The measures count movements (`arrivals` and `departures`) *not* flights. Counting flights per airline across all airports would count the 503 domestic flights twice.

- **Note:** The `API` spec also has `DIV`(Diverted) and `RER`(Rerouted) according to docs. But **none** of these codes have been found in the data spanning over these four days, but the status rule only counts `LAN` / `ACT`.

## 7. Date: which day does the fact carry?
- Four candidate dates per flight. Compared with the Swedish date of the scheduled time at the Swedavia airport, this many flights would land on another day (of 1 769 arrivals, 1 758 departures):

| If the fact used... | Arrivals | Departures |
|---|---|---|
| UTC date of the scheduled time | 49 | 3 |
| `departure_date_utc` (the key date) | 75 | 3 |
| Swedish date of the actual time | 16 | 2 |

- Arrivals move most: late evening flights landing after midnight, and long-haul flights that left the day before.
- The actual time moves late flights to the next day and early ones to the day before. Cancelled flights have no actual time, so they would have no date at all.

**For the model (proposal):** the fact carries the Swedish date of the scheduled time at the Swedavia airport, converted with the time zone name (`Europe/Stockholm`), never a fixed +2 hours, since Sweden moves to UTC+1 on 25 October. `departure_date_utc` stays in the key, where it identifies the flight.

## 8. Keys against Wikipedia: IATA or ICAO?
*Open*

## Not investigated yet
- 5 departures on 5 Oct still `SCH` two days later: warn, or filter silently?