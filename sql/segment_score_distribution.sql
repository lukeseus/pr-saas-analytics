-- observation A. analyzing avg health score v. NRR and gross retention by customer segmentation

select
    h.customer_level_segment,
    count(distinct h.mr_customer_id) as customers,
    round(avg(h.v3_health_score), 2) as avg_health_score,
    round(sum(r.arr_cy) / nullif(sum(r.arr_py), 0), 2) as nrr,
    round(sum(r.min_arr_for_gross) / nullif(sum(r.arr_py), 0), 2) as gross_retention
from 
    MUCK_RACK_CASE.ANALYTICS.TRF_V3_HEALTH_SCORE_DAILY h
inner join 
    MUCK_RACK_CASE.ANALYTICS.MRT_RETENTION_REPORTING_MONTHLY r
    on h.mr_customer_id = r.mr_customer_id
where 
    h.measurement_date = '2024-11-01'
group by 
    1
order by 
    avg_health_score desc;