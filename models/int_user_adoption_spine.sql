-- int_user_adoption_spine.sql
-- grain: one row per customer per day
-- rolls up user-level activity into account-level signals
-- feeds mart_customer_retention_risk

with user_activity as (

    select
        measurement_date,
        mr_customer_id,
        customer_level_segment,
        paid_users_sold,
        arr,
        platform_arr,
        broadcast_arr,
        keyhole_arr,
        lexisnexis_arr,
        managed_services_arr,
        press_release_arr,
        next_renewal_date,

        -- user-level feature category flags (research / monitoring / relationship)
        user_id,
        is_active_today,
        case when did_search_today then 1 else 0 end as uses_research,
        case
            when did_view_coverage_report_today
                or did_view_dashboard_today
                or did_create_alert_today
            then 1 else 0
        end as uses_monitoring,
        case
            when did_create_media_list_today
                or did_pitch_today
            then 1 else 0
        end as uses_relationship

    from {{ ref('trf_user_daily_features') }}

),

user_breadth as (

    select
        measurement_date,
        mr_customer_id,
        user_id,
        paid_users_sold,
        is_active_today,
        (uses_research + uses_monitoring + uses_relationship) as categories_used,
        case
            when (uses_research + uses_monitoring + uses_relationship) = 3
            then 1 else 0
        end as is_full_breadth_user

    from user_activity
    where is_active_today = true

),

account_adoption as (

    -- aggregate to customer-day grain
    select
        measurement_date,
        mr_customer_id,
        max(paid_users_sold) as paid_users_sold,
        count(distinct user_id) as active_users_today,
        sum(is_full_breadth_user) as full_breadth_users_today,

        -- seat penetration: what % of paid seats are active
        round(
            count(distinct user_id) / nullif(max(paid_users_sold), 0),
            3
        ) as seat_penetration_rate,

        -- breadth penetration: of active users, what % touch all 3 categories
        round(
            sum(is_full_breadth_user) / nullif(count(distinct user_id), 0),
            3
        ) as full_breadth_penetration_rate

    from user_breadth
    group by 1, 2

),

customer_spine as (

    -- one row per customer per day with all ARR and metadata
    select distinct
        measurement_date,
        mr_customer_id,
        customer_level_segment,
        paid_users_sold,
        arr,
        platform_arr,
        broadcast_arr
            + keyhole_arr
            + lexisnexis_arr
            + managed_services_arr
            + press_release_arr as addon_arr,
        broadcast_arr,
        keyhole_arr,
        next_renewal_date,
        datediff('day', measurement_date, next_renewal_date) as days_to_renewal

    from user_activity

)

select
    s.measurement_date,
    s.mr_customer_id,
    s.customer_level_segment,
    s.paid_users_sold,
    s.arr,
    s.platform_arr,
    s.addon_arr,
    s.broadcast_arr,
    s.keyhole_arr,
    round(s.addon_arr / nullif(s.arr, 0), 3) as addon_arr_pct,
    s.next_renewal_date,
    s.days_to_renewal,
    coalesce(a.active_users_today, 0) as active_users_today,
    coalesce(a.full_breadth_users_today, 0) as full_breadth_users_today,
    coalesce(a.seat_penetration_rate, 0) as seat_penetration_rate,
    coalesce(a.full_breadth_penetration_rate, 0) as full_breadth_penetration_rate

from customer_spine s
left join account_adoption a
    on s.mr_customer_id = a.mr_customer_id
    and s.measurement_date = a.measurement_date
