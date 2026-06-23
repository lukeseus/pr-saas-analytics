import csv
import random
import math
from datetime import date, timedelta

random.seed(42)

# --- Config ---
NUM_CUSTOMERS = 300
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 12, 31)
MONTHS = [date(2024, m, 1) for m in range(1, 13)]

SEGMENTS = [
    "Enterprise Brand", "Mid-Market Brand", "Emerging Brand",
    "Large Agency", "Boutique Agency", "Solo Agency"
]
INDUSTRIES = [
    "Technology", "Healthcare", "Finance", "Consumer Goods",
    "Entertainment", "Nonprofit", "Government", "Retail", "Energy"
]
CSM_TEAMS = ["Enterprise CS", "Mid-Market CS", "SMB CS", "Agency CS"]

# --- Helper functions ---
def rand_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]

# --- Customer master ---
customers = []
for i in range(NUM_CUSTOMERS):
    seg = weighted_choice(SEGMENTS, [15, 20, 20, 15, 20, 10])
    
    # ARR by segment — realistic ranges
    if seg == "Enterprise Brand":
        arr = round(random.uniform(80000, 300000), 2)
        paid_seats = random.randint(20, 80)
    elif seg == "Mid-Market Brand":
        arr = round(random.uniform(20000, 79999), 2)
        paid_seats = random.randint(8, 25)
    elif seg == "Emerging Brand":
        arr = round(random.uniform(5000, 19999), 2)
        paid_seats = random.randint(2, 10)
    elif seg == "Large Agency":
        arr = round(random.uniform(40000, 200000), 2)
        paid_seats = random.randint(15, 60)
    elif seg == "Boutique Agency":
        arr = round(random.uniform(10000, 39999), 2)
        paid_seats = random.randint(4, 15)
    else:  # Solo Agency
        arr = round(random.uniform(2000, 9999), 2)
        paid_seats = random.randint(1, 3)

    # Add-on ARR — Enterprise much more likely to carry add-ons (key to Observation A)
    broadcast_arr = 0
    keyhole_arr = 0
    lexisnexis_arr = 0
    managed_arr = 0
    pr_arr = 0

    if seg == "Enterprise Brand":
        if random.random() < 0.65:
            broadcast_arr = round(random.uniform(10000, 60000), 2)
        if random.random() < 0.55:
            keyhole_arr = round(random.uniform(8000, 40000), 2)
        if random.random() < 0.40:
            lexisnexis_arr = round(random.uniform(5000, 25000), 2)
        if random.random() < 0.25:
            managed_arr = round(random.uniform(10000, 50000), 2)
    elif seg in ("Large Agency", "Mid-Market Brand"):
        if random.random() < 0.30:
            broadcast_arr = round(random.uniform(5000, 20000), 2)
        if random.random() < 0.25:
            keyhole_arr = round(random.uniform(3000, 15000), 2)
    
    if random.random() < 0.15:
        pr_arr = round(random.uniform(1000, 8000), 2)

    platform_arr = round(arr * 0.7, 2)
    addon_arr = broadcast_arr + keyhole_arr + lexisnexis_arr + managed_arr + pr_arr
    
    # Deal type ARR
    deal_type = weighted_choice(["new", "renewal", "upsell", "expansion", "downsell"],
                                 [20, 50, 15, 10, 5])
    nb_arr = arr if deal_type == "new" else 0
    ren_arr = arr if deal_type == "renewal" else 0
    ups_arr = arr if deal_type == "upsell" else 0
    exp_arr = arr if deal_type == "expansion" else 0
    down_arr = arr if deal_type == "downsell" else 0

    # Tenure and renewal
    first_day = rand_date(date(2020, 1, 1), date(2023, 6, 1))
    renewal = rand_date(date(2025, 1, 1), date(2025, 12, 31))

    # Usage profile — determines health score and retention (key structural driver)
    # Enterprise: high adoption score but add-on risk
    # Seasonal agencies: campaign-driven usage (key to Observation C)
    is_seasonal = seg in ("Large Agency", "Boutique Agency") and random.random() < 0.45
    
    # Seat penetration — core to Observation B
    if seg == "Enterprise Brand":
        # Wide seats, but penetration varies — some have power user clusters only
        deep_penetration = random.random() < 0.40  # only 40% have truly deep adoption
    elif seg == "Mid-Market Brand":
        deep_penetration = random.random() < 0.65
    else:
        deep_penetration = random.random() < 0.55

    customers.append({
        "mr_customer_id": f"CUS_{i+1:04d}",
        "segment": seg,
        "industry": random.choice(INDUSTRIES),
        "csm_team": CSM_TEAMS[0] if seg == "Enterprise Brand" else
                    CSM_TEAMS[1] if seg == "Mid-Market Brand" else
                    CSM_TEAMS[3] if "Agency" in seg else CSM_TEAMS[2],
        "csm_email": f"csm_{random.randint(1,12)}@muckrack.com",
        "paid_seats": paid_seats,
        "arr": arr,
        "platform_arr": platform_arr,
        "broadcast_arr": broadcast_arr,
        "keyhole_arr": keyhole_arr,
        "lexisnexis_arr": lexisnexis_arr,
        "managed_services_arr": managed_arr,
        "press_release_arr": pr_arr,
        "newbusiness_arr": nb_arr,
        "renewal_arr": ren_arr,
        "upsell_arr": ups_arr,
        "expansion_arr": exp_arr,
        "downsell_arr": down_arr,
        "first_day_as_customer_date": first_day,
        "next_renewal_date": renewal,
        "is_seasonal": is_seasonal,
        "deep_penetration": deep_penetration,
        "addon_arr": addon_arr,
    })

print(f"Generated {len(customers)} customers")

# --- Table 1: trf_user_daily_features ---
# Sample 30 days of data (full year would be huge; 30 days is enough for SQL demos)
SAMPLE_DATES = [date(2024, 11, 1) + timedelta(days=i) for i in range(30)]

print("Generating user daily features...")
user_rows = []
for cust in customers:
    seg = cust["segment"]
    is_seasonal = cust["is_seasonal"]
    deep = cust["deep_penetration"]
    
    num_users = max(1, int(cust["paid_seats"] * random.uniform(0.6, 1.0)))
    
    for user_idx in range(num_users):
        user_id = int(cust["mr_customer_id"].replace("CUS_", "")) * 1000 + user_idx
        
        # User type: power user vs light user (critical for Observation B)
        is_power_user = (user_idx < max(1, int(num_users * (0.7 if deep else 0.2))))
        
        for d in SAMPLE_DATES:
            # Seasonal customers: high activity early in month (campaign burst), low late
            if is_seasonal:
                day_of_month = d.day
                activity_prob = 0.75 if day_of_month <= 10 else 0.20
            elif is_power_user:
                activity_prob = 0.70
            else:
                activity_prob = 0.25
            
            is_active = random.random() < activity_prob
            
            if is_active and is_power_user:
                did_search = random.random() < 0.80
                did_media_list = random.random() < 0.65
                did_pitch = random.random() < 0.55
                did_coverage = random.random() < 0.60
                did_dashboard = random.random() < 0.45
                did_alert = random.random() < 0.50
            elif is_active:
                did_search = random.random() < 0.70  # light users mostly just search
                did_media_list = random.random() < 0.20
                did_pitch = random.random() < 0.15
                did_coverage = random.random() < 0.20
                did_dashboard = random.random() < 0.15
                did_alert = random.random() < 0.10
            else:
                did_search = did_media_list = did_pitch = False
                did_coverage = did_dashboard = did_alert = False

            user_rows.append({
                "measurement_date": d,
                "mr_customer_id": cust["mr_customer_id"],
                "user_id": user_id,
                "customer_level_segment": cust["segment"],
                "industry": cust["industry"],
                "csm_email": cust["csm_email"],
                "csm_team": cust["csm_team"],
                "paid_users_sold": cust["paid_seats"],
                "arr": cust["arr"],
                "platform_arr": cust["platform_arr"],
                "broadcast_arr": cust["broadcast_arr"],
                "keyhole_arr": cust["keyhole_arr"],
                "lexisnexis_arr": cust["lexisnexis_arr"],
                "managed_services_arr": cust["managed_services_arr"],
                "press_release_arr": cust["press_release_arr"],
                "newbusiness_arr": cust["newbusiness_arr"],
                "renewal_arr": cust["renewal_arr"],
                "upsell_arr": cust["upsell_arr"],
                "expansion_arr": cust["expansion_arr"],
                "downsell_arr": cust["downsell_arr"],
                "is_active_today": is_active,
                "did_search_today": did_search,
                "did_create_media_list_today": did_media_list,
                "did_pitch_today": did_pitch,
                "did_view_coverage_report_today": did_coverage,
                "did_view_dashboard_today": did_dashboard,
                "did_create_alert_today": did_alert,
                "next_renewal_date": cust["next_renewal_date"],
            })

print(f"Generated {len(user_rows)} user-day rows")

# --- Table 2: trf_v3_health_score_daily ---
print("Generating health scores...")
health_rows = []
HEALTH_DATES = [date(2024, 11, 1) + timedelta(days=i) for i in range(30)]

for cust in customers:
    seg = cust["segment"]
    deep = cust["deep_penetration"]
    is_seasonal = cust["is_seasonal"]
    
    for d in HEALTH_DATES:
        # percent_days_active_score (0-10): Enterprise tends higher
        if seg == "Enterprise Brand":
            pct_active = round(random.uniform(0.55, 0.95), 3)
        elif seg == "Mid-Market Brand":
            pct_active = round(random.uniform(0.40, 0.85), 3) if deep else round(random.uniform(0.25, 0.60), 3)
        elif is_seasonal:
            # Seasonal: good overall but volatile — key to Obs C
            pct_active = round(random.uniform(0.35, 0.75), 3)
        else:
            pct_active = round(random.uniform(0.20, 0.70), 3)
        
        pct_active_score = round(pct_active * 10, 2)
        
        # feature_categories_used (0-3): account-level, masks penetration issue (Obs B)
        if seg == "Enterprise Brand":
            # High score even without deep penetration — power user cluster drives it
            feat_cats = 3 if random.random() < 0.85 else 2
        elif deep:
            feat_cats = 3 if random.random() < 0.70 else 2
        else:
            feat_cats = random.choices([1, 2, 3], weights=[30, 45, 25])[0]
        
        feat_score = float(feat_cats)
        
        # net_positive_periods (-12 to +12): seasonal customers show volatile/negative
        if is_seasonal:
            # Campaign cycle creates artificial declines — Observation C
            net_pp = random.randint(-8, 6)
        elif deep and seg in ("Mid-Market Brand", "Emerging Brand"):
            net_pp = random.randint(2, 10)
        elif seg == "Enterprise Brand":
            net_pp = random.randint(0, 8)
        else:
            net_pp = random.randint(-4, 8)
        
        # Score components
        net_pp_score = float(net_pp)
        v3_score = round(pct_active_score + feat_score + net_pp_score, 2)
        
        health_rows.append({
            "measurement_date": d,
            "mr_customer_id": cust["mr_customer_id"],
            "v3_health_score": v3_score,
            "percent_days_active_score": pct_active_score,
            "feature_categories_used_score": feat_score,
            "net_positive_periods_score": net_pp_score,
            "percent_days_active": round(pct_active * 100, 2),
            "feature_categories_used": feat_cats,
            "net_positive_periods": net_pp,
            "customer_level_segment": seg,
            "arr": cust["arr"],
        })

print(f"Generated {len(health_rows)} health score rows")

# --- Table 3: mrt_retention_reporting_monthly ---
print("Generating retention data...")
retention_rows = []

for cust in customers:
    seg = cust["segment"]
    deep = cust["deep_penetration"]
    addon_arr = cust["addon_arr"]
    arr = cust["arr"]
    
    for month in MONTHS:
        arr_py = round(arr * random.uniform(0.85, 1.15), 2)
        
        # Retention logic — the structural insight for Observation A
        # Enterprise: platform usage looks great but add-ons get shed
        if seg == "Enterprise Brand":
            if addon_arr > 30000:
                # High add-on exposure — more likely to shed at renewal
                retention_factor = random.uniform(0.72, 1.05)
            else:
                retention_factor = random.uniform(0.88, 1.15)
        elif seg == "Mid-Market Brand":
            # Mid-market: mostly platform ARR, retention follows usage
            if deep:
                retention_factor = random.uniform(0.92, 1.20)
            else:
                retention_factor = random.uniform(0.75, 1.05)
        elif seg in ("Large Agency", "Boutique Agency"):
            # Agencies: seasonal but sticky if campaign-driven
            retention_factor = random.uniform(0.80, 1.10)
        else:
            retention_factor = random.uniform(0.70, 1.10)
        
        arr_cy = round(arr_py * retention_factor, 2)
        min_arr = round(min(arr_py, arr_cy), 2)
        
        platform_py = round(arr_py * 0.70, 2)
        platform_cy = round(arr_cy * 0.70, 2)
        
        # Add-on ARR — Enterprise more likely to shed broadcast/keyhole
        broadcast_py = cust["broadcast_arr"]
        broadcast_cy = round(broadcast_py * random.uniform(0.0 if (seg == "Enterprise Brand" and addon_arr > 30000) else 0.7, 1.1), 2)

        retention_rows.append({
            "measurement_date": month,
            "mr_customer_id": cust["mr_customer_id"],
            "arr_py": arr_py,
            "arr_cy": arr_cy,
            "min_arr_for_gross": min_arr,
            "platform_arr_py": platform_py,
            "platform_arr_cy": platform_cy,
            "broadcast_arr_py": broadcast_py,
            "broadcast_arr_cy": broadcast_cy,
            "customer_level_segment": seg,
            "customer_level_business_type": "Agency" if "Agency" in seg else "Brand",
            "first_day_as_customer_date": cust["first_day_as_customer_date"],
            "next_renewal_date": cust["next_renewal_date"],
        })

print(f"Generated {len(retention_rows)} retention rows")

# --- Table 4: mrt_feature_objects_current_customers ---
print("Generating feature object counts...")
feature_rows = []

for cust in customers:
    deep = cust["deep_penetration"]
    seg = cust["segment"]
    
    for d in HEALTH_DATES:
        # Total objects vs active objects — the ghost dashboard problem
        if deep:
            alert_total = random.randint(5, 40)
            cr_total = random.randint(3, 25)
            dash_total = random.randint(2, 20)
            ml_total = random.randint(5, 50)
            pitch_total = random.randint(10, 100)
            active_ratio = random.uniform(0.55, 0.90)
        else:
            # Enterprise: lots of objects, low active ratio (ghost dashboards — Obs B signal)
            if seg == "Enterprise Brand":
                alert_total = random.randint(10, 80)
                cr_total = random.randint(5, 40)
                dash_total = random.randint(5, 50)  # high total, low active
                ml_total = random.randint(10, 80)
                pitch_total = random.randint(20, 150)
                active_ratio = random.uniform(0.10, 0.35)  # ghost objects
            else:
                alert_total = random.randint(1, 15)
                cr_total = random.randint(1, 10)
                dash_total = random.randint(1, 12)
                ml_total = random.randint(2, 20)
                pitch_total = random.randint(3, 40)
                active_ratio = random.uniform(0.30, 0.65)

        feature_rows.append({
            "measurement_date": d,
            "mr_customer_id": cust["mr_customer_id"],
            "alert_object_count": alert_total,
            "coverage_report_object_count": cr_total,
            "automated_coverage_report_object_count": int(cr_total * 0.4),
            "active_coverage_report_object_count": max(0, int(cr_total * active_ratio)),
            "dashboard_object_count": dash_total,
            "active_dashboard_object_count": max(0, int(dash_total * active_ratio)),
            "media_list_object_count": ml_total,
            "active_media_list_object_count": max(0, int(ml_total * active_ratio)),
            "pitch_object_count": pitch_total,
            "presentation_object_count": random.randint(0, 10),
            "saved_search_object_count": random.randint(2, 30),
        })

print(f"Generated {len(feature_rows)} feature object rows")

# --- Write CSVs ---
import os
os.makedirs("/home/claude/seed_data", exist_ok=True)

def write_csv(filename, rows):
    if not rows:
        return
    with open(f"/home/claude/seed_data/{filename}", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows to {filename}")

write_csv("trf_user_daily_features.csv", user_rows)
write_csv("trf_v3_health_score_daily.csv", health_rows)
write_csv("mrt_retention_reporting_monthly.csv", retention_rows)
write_csv("mrt_feature_objects_current_customers.csv", feature_rows)

print("\nAll seed data written to /home/claude/seed_data/")
