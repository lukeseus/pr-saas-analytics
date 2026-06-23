-- proposed new metric: seat penetration rate. what % of paid seats are actually active
with daily_seats as (
    select
        measurement_date,
        mr_customer_id,
        customer_level_segment,
        paid_users_sold,
        count(distinct user_id) as active_users
    from
        MUCK_RACK_CASE.ANALYTICS.TRF_USER_DAILY_FEATURES
    where
        is_active_today = true
    group by
        1,
        2,
        3,
        4
)
select
    customer_level_segment,
    round(
        avg(active_users / nullif(paid_users_sold, 0)),
        3
    ) as avg_seat_penetration,
    count(distinct mr_customer_id) as customers
from
    daily_seats
group by
    1
order by
    avg_seat_penetration desc;