-- what's the add-on exposure by segment 
select
    customer_level_segment,
    count(distinct mr_customer_id) as customers,
    round(avg(arr), 0) as avg_arr,
    round(
        avg(
            broadcast_arr + keyhole_arr + lexisnexis_arr + managed_services_arr + press_release_arr
        ),
        0
    ) as avg_add_on_arr,
    round(
        avg(
            broadcast_arr + keyhole_arr + lexisnexis_arr + managed_services_arr + press_release_arr
        ) / nullif(avg(arr), 0),
        3
    ) as add_on_pct_of_arr
from
    MUCK_RACK_CASE.ANALYTICS.TRF_USER_DAILY_FEATURES
where
    measurement_date = '2024-11-01'
group by
    1
order by
    addon_pct_of_arr desc;