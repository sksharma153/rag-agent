-- ============================================================
-- dq_ml_features.sql
-- Curated model-ready feature set for Isolation Forest.
--
-- Input:
--   sab-dev-dap-lakehouse-1470.data_quality.dq_feature_complete
--
-- Output:
--   sab-dev-dap-lakehouse-1470.data_quality.dq_ml_features
--
-- The aliases below intentionally match the Python
-- MODEL_FEATURES list used by feature_engineering.py.
-- ============================================================

CREATE OR REPLACE TABLE
  `sab-dev-dap-lakehouse-1470.data_quality.dq_ml_features`
PARTITION BY DATE(metric_timestamp)
CLUSTER BY table_name
AS

WITH base AS (
  SELECT
    table_name,
    metric_timestamp,

    -- ==========================================================
    -- Volume / statistical anomaly features
    -- ==========================================================
    row_count,

    SAFE_DIVIDE(
      row_count - AVG(row_count) OVER (),
      NULLIF(STDDEV(row_count) OVER (), 0)
    ) AS row_count_score,

    SAFE_DIVIDE(
      distinct_event_count - AVG(distinct_event_count) OVER (),
      NULLIF(STDDEV(distinct_event_count) OVER (), 0)
    ) AS event_count_zscore,

    SAFE_DIVIDE(
      active_pax_avg - AVG(active_pax_avg) OVER (),
      NULLIF(STDDEV(active_pax_avg) OVER (), 0)
    ) AS active_pax_zscore,

    SAFE_DIVIDE(
      avg_ingestion_latency_seconds
        - AVG(avg_ingestion_latency_seconds) OVER (),
      NULLIF(STDDEV(avg_ingestion_latency_seconds) OVER (), 0)
    ) AS ingestion_latency_zscore,

    SAFE_DIVIDE(
      order_total_avg - AVG(order_total_avg) OVER (),
      NULLIF(STDDEV(order_total_avg) OVER (), 0)
    ) AS order_total_zscore,

    -- ==========================================================
    -- Detailed DQ domain ratios
    -- ==========================================================
    root_fields_null_ratio,
    financial_fields_null_ratio,
    conditional_violation_ratio,
    item_fields_null_ratio,
    service_critical_fields_null_ratio,
    segment_fields_null_ratio,
    payment_fields_null_ratio,
    passenger_fields_null_ratio,

    -- ==========================================================
    -- Structural counts
    -- ==========================================================
    total_order_items,
    total_payments,
    total_passengers,
    total_services,
    total_conditional_violations,

    -- ==========================================================
    -- Business-rule flags
    -- ==========================================================
    flag_missing_all_items,
    flag_missing_all_passengers,
    flag_missing_all_services,
    flag_cancelled_missing_reason,
    flag_item_amt_without_ccy,
    flag_item_base_amt_without_ccy,
    flag_active_svc_missing_ticket,
    flag_flight_missing_times,
    flag_flight_missing_legs,
    flag_pay_amt_without_ccy,

    -- ==========================================================
    -- Calendar / missing-hour features
    -- ==========================================================
    is_missing_hour,
    hour_of_day,
    day_of_week

  FROM
    `sab-dev-dap-lakehouse-1470.data_quality.dq_feature_complete`
)

SELECT
  table_name,
  metric_timestamp,

  row_count_score,
  event_count_zscore,
  active_pax_zscore,
  ingestion_latency_zscore,
  order_total_zscore,

  root_fields_null_ratio,
  financial_fields_null_ratio,
  conditional_violation_ratio,
  item_fields_null_ratio,
  service_critical_fields_null_ratio,
  segment_fields_null_ratio,
  payment_fields_null_ratio,
  passenger_fields_null_ratio,

  total_order_items,
  total_payments,
  total_passengers,
  total_services,
  total_conditional_violations,

  flag_missing_all_items,
  flag_missing_all_passengers,
  flag_missing_all_services,
  flag_cancelled_missing_reason,
  flag_item_amt_without_ccy,
  flag_item_base_amt_without_ccy,
  flag_active_svc_missing_ticket,
  flag_flight_missing_times,
  flag_flight_missing_legs,
  flag_pay_amt_without_ccy,

  is_missing_hour,

  -- Cyclical time encoding
  SIN(2 * PI() * hour_of_day / 24.0) AS hour_sin,
  COS(2 * PI() * hour_of_day / 24.0) AS hour_cos,

  SIN(2 * PI() * day_of_week / 7.0) AS day_of_week_sin,
  COS(2 * PI() * day_of_week / 7.0) AS day_of_week_cos

FROM base;
