-- Observation B: feature breadth at user level vs account level. An account scores 3/3 if any one user touches each category

with user_categories as (
    select
        mr_customer_id,
        user_id,
        paid_users_sold,
        case
            when did_search_today then 1
            else 0
        end as research,
        case
            when did_view_coverage_report_today
            or did_view_dashboard_today
            or did_create_alert_today then 1
            else 0
        end as monitoring,
        case
            when did_create_media_list_today
            or did_pitch_today then 1
            else 0
        end as relationship
    from
        MUCK_RACK_CASE.ANALYTICS.TRF_USER_DAILY_FEATURES
    where
        is_active_today = true
        and measurement_date = '2024-11-01'
),
-- this cte will highlight users with full breadth across the different categories
user_breadth as (
    select
        mr_customer_id,
        user_id,
        paid_users_sold,
        (research + monitoring + relationship) as categories_used,
        case
            when (research + monitoring + relationship) = 3 then 1
            else 0
        end as full_breadth
    from
        user_categories
),
account_level as (
    select
        mr_customer_id,
        paid_users_sold,
        count(distinct user_id) as active_users,
        round(count(distinct user_id) / paid_users_sold, 3) as seat_utilization,
        sum(full_breadth) as full_breadth_users,
        -- percent of users with full breadth
        round(
            sum(full_breadth) / nullif(count(distinct user_id), 0),
            3
        ) as breadth_penetration
    from
        user_breadth
    group by
        1,
        2
)
select
    u.customer_level_segment,
    -- account-level score from health model 
    h.feature_categories_used_score,
    round(avg(a.seat_utilization), 3) as avg_seat_utilization,
    -- this is what v3 can't see, how many users actually have full breadth
    round(avg(a.breadth_penetration), 3) as avg_full_breadth_penetration,
    count(distinct a.mr_customer_id) as customers
from
    account_level a
join
    MUCK_RACK_CASE.ANALYTICS.TRF_USER_DAILY_FEATURES u 
on 
    a.mr_customer_id = u.mr_customer_id
    and u.measurement_date = '2024-11-01'
join 
    MUCK_RACK_CASE.ANALYTICS.TRF_V3_HEALTH_SCORE_DAILY h 
on 
    a.mr_customer_id = h.mr_customer_id
    and h.measurement_date = '2024-11-01'
group by
    1,
    2
order by
    1,
    2;