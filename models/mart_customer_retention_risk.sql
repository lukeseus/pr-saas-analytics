-- mart_customer_retention_risk.sql
-- grain: one row per customer per day
-- supplements health score v3 with three signals it can't see:
--   1. add-on ARR exposure (observation A)
--   2. seat-level breadth penetration (observation B)
--   3. activity relative to customer's own baseline (observation C)

with adoption as (

    select * from {{ ref('int_user_adoption_spine') }}

),

health as (

    select
        measurement_date,
        mr_customer_id,
        v3_health_score,
        percent_days_active_score,
        feature_categories_used_score,
        net_positive_periods_score,
        percent_days_active,
        feature_categories_used,
        net_positive_periods

    from {{ ref('trf_v3_health_score_daily') }}

),

feature_objects as (

    select
        measurement_date,
        mr_customer_id,
        dashboard_object_count,
        active_dashboard_object_count,
        coverage_report_object_count,
        active_coverage_report_object_count,
        media_list_object_count,
        active_media_list_object_count,

        -- ratio of active to total objects — ghost dashboard signal
        round(
            (
                active_dashboard_object_count
                + active_coverage_report_object_count
                + active_media_list_object_count
            ) / nullif(
                dashboard_object_count
                + coverage_report_object_count
                + media_list_object_count,
                0
            ),
            3
        ) as active_object_ratio

    from {{ ref('mrt_feature_objects_current_customers') }}

),

-- customer's own trailing activity baseline for observation C
-- compares current activity to their own historical median, not an absolute threshold
activity_baseline as (

    select
        mr_customer_id,
        measurement_date,
        percent_days_active,
        avg(percent_days_active) over (
            partition by mr_customer_id
            order by measurement_date
            rows between 364 preceding and 1 preceding
        ) as trailing_365d_median_activity

    from health

),

joined as (

    select
        a.measurement_date,
        a.mr_customer_id,
        a.customer_level_segment,
        a.arr,
        a.platform_arr,
        a.addon_arr,
        a.addon_arr_pct,
        a.broadcast_arr,
        a.keyhole_arr,
        a.paid_users_sold,
        a.active_users_today,
        a.seat_penetration_rate,
        a.full_breadth_users_today,
        a.full_breadth_penetration_rate,
        a.next_renewal_date,
        a.days_to_renewal,

        -- v3 signals (kept for context, not replaced)
        h.v3_health_score,
        h.percent_days_active,
        h.feature_categories_used,
        h.net_positive_periods,

        -- observation C: activity vs customer's own baseline
        b.trailing_365d_median_activity,
        round(
            h.percent_days_active - b.trailing_365d_median_activity,
            2
        ) as activity_vs_baseline,

        -- object engagement depth
        fo.active_object_ratio

    from adoption a
    left join health h
        on a.mr_customer_id = h.mr_customer_id
        and a.measurement_date = h.measurement_date
    left join activity_baseline b
        on a.mr_customer_id = b.mr_customer_id
        and a.measurement_date = b.measurement_date
    left join feature_objects fo
        on a.mr_customer_id = fo.mr_customer_id
        and a.measurement_date = fo.measurement_date

),

risk_tiered as (

    select
        *,

        -- high risk conditions — any one triggers
        case
            when addon_arr_pct > 0.20 and days_to_renewal < 90 then 1
            when seat_penetration_rate < 0.30 and paid_users_sold > 15 then 1
            when full_breadth_penetration_rate < 0.25 and arr > 50000 then 1
            when activity_vs_baseline < -15 then 1
            else 0
        end as is_high_risk,

        -- medium risk: two or more softer signals
        (
            case when addon_arr_pct > 0.15 then 1 else 0 end
            + case when seat_penetration_rate < 0.40 then 1 else 0 end
            + case when activity_vs_baseline < -8 then 1 else 0 end
            + case when active_object_ratio < 0.30 then 1 else 0 end
        ) as medium_risk_signal_count

    from joined

)

select
    measurement_date,
    mr_customer_id,
    customer_level_segment,
    arr,
    platform_arr,
    addon_arr,
    addon_arr_pct,
    broadcast_arr,
    keyhole_arr,
    paid_users_sold,
    active_users_today,
    seat_penetration_rate,
    full_breadth_users_today,
    full_breadth_penetration_rate,
    next_renewal_date,
    days_to_renewal,
    v3_health_score,
    percent_days_active,
    feature_categories_used,
    net_positive_periods,
    trailing_365d_median_activity,
    activity_vs_baseline,
    active_object_ratio,

    -- final risk tier
    case
        when is_high_risk = 1 then 'High'
        when medium_risk_signal_count >= 2 then 'Medium'
        else 'Low'
    end as risk_tier,

    -- human-readable flag for CS teams
    case
        when addon_arr_pct > 0.20 and days_to_renewal < 90
            then 'Add-on ARR at risk — renewal within 90 days'
        when seat_penetration_rate < 0.30 and paid_users_sold > 15
            then 'Low seat penetration on large account'
        when full_breadth_penetration_rate < 0.25 and arr > 50000
            then 'Workflow not embedded — power user dependency'
        when activity_vs_baseline < -15
            then 'Activity significantly below own baseline'
        else null
    end as primary_risk_reason

from risk_tiered
