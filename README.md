# PR SaaS Analytics — Case Study

Analytics case study submission 


---

## What's in this repo

```
pr-saas-analytics/
├── sql/
│   ├── segment_score_distribution.sql   # observation A: health score vs NRR by segment
│   ├── segment_add_on_arr.sql           # observation A: add-on ARR exposure by segment
│   ├── segment_feature_breadth.sql      # observation B: seat utilization vs full-breadth penetration
│   ├── seat_penetration.sql             # proposed new metric: seat penetration rate
│   └── seasonal_net_periods.sql         # observation C: net positive periods volatility
├── models/
│   ├── int_user_adoption_spine.sql      # intermediate model: user activity → account grain
│   ├── mart_customer_retention_risk.sql # proposed mart with risk tier logic
│   └── schema.yml                       # column docs and dbt tests
├── seed_data/
│   └── generate_seed_data.py            # generates synthetic CSVs matching case study schemas
└── deliverables/
    └── muck_rack_case_study_luke_seus.pdf
```

## Approach

All analysis was run against a synthetic dataset I generated to match the four table schemas provided in the case study. The data was loaded into a Snowflake trial environment and queried directly — results in the written deliverable are screenshots from actual query output, not hypothetical numbers.

The synthetic data was designed to reflect the structural patterns described in each observation:

- **Observation A**: Enterprise accounts carry higher add-on ARR exposure, which creates a health score / NRR inversion
- **Observation B**: Account-level feature breadth scores mask low seat-level penetration, especially on large accounts
- **Observation C**: Agency accounts show higher net positive periods volatility due to campaign-driven usage cycles

## Running the queries

1. Spin up a Snowflake trial account
2. Run `sql/01_snowflake_setup.sql` to create the database, tables, and stages
3. Generate seed data: `python seed_data/generate_seed_data.py`
4. Load the CSVs via Snowflake's Upload Local Files interface
5. Run `sql/02_verify_and_observe.sql` — each query is annotated with the observation it supports

## dbt models

The `models/` folder contains the proposed supplementary mart. Written in standard dbt SQL with `{{ ref() }}` syntax — ready to drop into an existing dbt project. `schema.yml` includes column documentation and dbt tests (not_null, accepted_values, accepted_range, unique_combination_of_columns).

---

Luke Seus · [linkedin.com/in/lukeseus](https://linkedin.com/in/lukeseus) · June 2025
