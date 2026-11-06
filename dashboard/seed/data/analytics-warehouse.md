---
last_reviewed: 2024-06-03
owner: Karim El Sayed (Platform)
source: Notes from a 2024 data-platform walkthrough (not re-checked since)
---
# Analytics warehouse

- Product analytics land in the legacy **Redshift** cluster `analytics-prod`, loaded nightly
  at 02:00 UTC by the `etl-nightly` Airflow DAG.
- Ask in `#data-platform` for warehouse credentials. Karim El Sayed provisions them by hand.
- Dashboards are in Metabase. Copy the "Core KPIs" collection before you edit it.
- Planned: move to a new warehouse "sometime in 2025".
