with date_spine as (
    select range::date as date_day
    from range(date '1970-01-01', date '2031-01-01', interval '1 day')
)
select
    row_number() over (order by date_day)                                   as date_key,
    date_day,
    year(date_day)                                                          as year,
    quarter(date_day)                                                       as quarter,
    month(date_day)                                                         as month_number,
    monthname(date_day)                                                     as month_name,
    day(date_day)                                                           as day_of_month,
    dayofweek(date_day)                                                     as day_of_week,
    dayname(date_day)                                                       as day_name,
    weekofyear(date_day)                                                    as week_of_year,
    year(date_day)::varchar || '-Q' || quarter(date_day)::varchar           as year_quarter
from date_spine
