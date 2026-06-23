-- Observation C: net positive periods is volatile for seasonal customers. Customers with negative trend scores but healthy activity levels

select
    customer_level_segment,
    count(distinct mr_customer_id) as customers,
    round(avg(net_positive_periods), 2) as avg_net_positive_periods,
    round(stddev(net_positive_periods), 2) as std_dev_npp,
    round(avg(percent_days_active), 2) as avg_pct_days_active,
    -- flagged as declining but still meaningfully active — false negatives
    sum(
        case
            when net_positive_periods < 0
            and percent_days_active > 40 then 1
            else 0
        end
    ) as active_but_trend_negative
from
    MUCK_RACK_CASE.ANALYTICS.TRF_V3_HEALTH_SCORE_DAILY
where
    measurement_date = '2024-11-01'
group by
    1
order by
    std_dev_npp desc;