-- One row per unique Swedish calendar date from flight movements.

with dates as (

    -- Get dates from arrivals.
    select date_key
    from {{ ref('stg_swedavia__arrivals') }}

    union -- Combine dates and remove duplicates.

    -- Get dates from departures.
    select date_key
    from {{ ref('stg_swedavia__departures') }}

)

select
    date_key,
    dayname(date_key) as weekday -- Get the weekday name.

from dates
where date_key is not null -- Exclude missing dates.