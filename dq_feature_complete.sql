-- ============================================================
-- dq_feature_complete.sql
-- Builds a complete hourly timeline from dq_feature.
--
-- Missing hours are represented explicitly:
--   row_count = 0
--   all other DQ metrics remain NULL
--   is_missing_hour = 1
-- ============================================================

CREATE OR REPLACE TABLE
  `sab-dev-dap-lakehouse-1470.data_quality.dq_feature_complete`
PARTITION BY DATE(metric_timestamp)
CLUSTER BY table_name
AS

WITH bounds AS (
  SELECT
    MIN(metric_timestamp) AS start_ts,
    MAX(metric_timestamp) AS end_ts
  FROM
    `sab-dev-dap-lakehouse-1470.data_quality.dq_feature`
),

expected_hours AS (
  SELECT
    metric_timestamp
  FROM bounds,
  UNNEST(
    GENERATE_TIMESTAMP_ARRAY(
      start_ts,
      end_ts,
      INTERVAL 1 HOUR
    )
  ) AS metric_timestamp
)

SELECT
  'order_history' AS table_name,
  e.metric_timestamp,

  -- Existing / volume
  COALESCE(f.row_count, 0) AS row_count,
  f.distinct_order_count,
  f.distinct_event_count,

  -- Existing completeness
  f.order_id_null_rate,
  f.order_version_null_rate,
  f.event_id_null_rate,
  f.order_type_null_rate,
  f.order_status_null_rate,

  -- Existing uniqueness
  f.business_key_duplicate_rate,
  f.event_id_duplicate_rate,

  -- Existing passenger metrics
  f.active_pax_avg,
  f.active_pax_stddev,
  f.active_pax_min,
  f.active_pax_max,
  f.active_pax_p50,
  f.active_pax_p95,
  f.active_pax_p99,

  -- Existing amount metrics
  f.order_total_avg,
  f.order_total_stddev,
  f.order_total_min,
  f.order_total_max,
  f.order_total_p50,
  f.order_total_p95,
  f.order_total_p99,
  f.negative_order_total_rate,
  f.negative_discount_rate,

  -- Existing timestamp / latency
  f.future_event_rate,
  f.invalid_ingestion_timestamp_rate,
  f.avg_ingestion_latency_seconds,
  f.ingestion_latency_p95,
  f.ingestion_latency_p99,

  -- Detailed root NULL indicators
  f.null_order_id,
  f.null_order_version,
  f.null_order_type_cd,
  f.null_order_status,
  f.null_order_change_actions,
  f.null_event_id,
  f.null_event_ts,
  f.null_last_update_event_ts,
  f.null_create_audit_event_ts,
  f.null_request_ts,
  f.null_response_ts,
  f.null_trip_type_cd,
  f.null_trip_origin_airport_cd,
  f.null_trip_destination_airport_cd,
  f.null_create_channel_cd,
  f.null_last_update_channel_cd,
  f.null_pos_channel_cd,
  f.null_pos_country_cd,
  f.null_active_pax_in_order,
  f.null_total_pax_in_order,
  f.null_paid_order_flag,
  f.null_migration_flag,
  f.null_source,
  f.null_retailer_order_id,
  f.null_retailer_owner_cd,

  -- Detailed financial NULL indicators
  f.null_order_total_amt,
  f.null_order_total_ccy,
  f.null_order_base_amt,
  f.null_order_base_ccy,
  f.null_order_total_tax_amt,
  f.null_order_total_tax_ccy,
  f.null_order_discount_amt,
  f.null_order_discount_ccy,
  f.null_order_base_equivalent_amt,
  f.null_order_base_equivalent_ccy,
  f.null_order_payment_balance,
  f.null_order_payment_balance_ccy,
  f.null_order_forfeited_total_amt,
  f.null_order_forfeited_total_ccy,

  -- Conditional rules
  f.flag_paid_but_missing_amt,
  f.flag_paid_but_missing_ccy,
  f.flag_error_without_code,
  f.flag_error_without_category,
  f.flag_closed_missing_balance,
  f.flag_pax_without_trip_type,
  f.flag_pax_without_trip_route,
  f.flag_total_amt_without_ccy,
  f.flag_base_amt_without_ccy,
  f.flag_tax_amt_without_ccy,
  f.flag_active_pax_exceeds_total,
  f.flag_paid_closed_no_payments,

  -- Structural arrays
  f.total_order_items,
  f.total_payments,
  f.total_passengers,
  f.change_action_count,
  f.price_class_count,
  f.distribution_chain_count,
  f.total_services,
  f.flag_missing_all_items,
  f.flag_missing_all_passengers,
  CASE
    WHEN f.row_count IS NULL THEN NULL
    WHEN f.total_services IS NULL OR f.total_services = 0 THEN 1
    ELSE 0
  END AS flag_missing_all_services,

  -- Item / service metrics
  f.null_item_ids,
  f.null_item_statuses,
  f.null_item_total_amts,
  f.null_item_total_ccys,
  f.null_item_base_amts,
  f.null_item_channels,
  f.flag_cancelled_missing_reason,
  f.flag_item_amt_without_ccy,
  f.flag_item_base_amt_without_ccy,

  f.null_ticket_numbers,
  f.null_fare_basis_codes,
  f.null_journey_departure_dts,
  f.null_journey_arrival_dts,
  f.null_segment_origins,
  f.null_segment_destinations,
  f.null_segment_departure_dts,
  f.null_segment_arrival_dts,
  f.null_marketing_carrier_cds,
  f.null_operating_carrier_cds,
  f.null_booking_class_cds,
  f.null_cabin_cds,
  f.null_passenger_ids_in_svc,
  f.null_service_ids,
  f.null_service_statuses,
  f.null_journey_ids,
  f.null_segment_ids,
  f.flag_active_svc_missing_ticket,
  f.flag_flight_missing_times,
  f.flag_flight_missing_legs,

  -- Payment metrics
  f.null_payment_ids,
  f.null_payment_statuses,
  f.null_payment_methods,
  f.null_payment_amts,
  f.null_payment_ccys,
  f.null_payment_timestamps,
  f.flag_pay_amt_without_ccy,

  -- Passenger metrics
  f.null_pax_ids,
  f.null_pax_ptc_cds,
  f.null_pax_first_names,
  f.null_pax_last_names,

  -- Domain ratios
  f.root_fields_null_ratio,
  f.financial_fields_null_ratio,
  f.conditional_violation_ratio,
  f.item_fields_null_ratio,
  f.service_critical_fields_null_ratio,
  f.segment_fields_null_ratio,
  f.payment_fields_null_ratio,
  f.passenger_fields_null_ratio,
  f.total_conditional_violations,

  -- Calendar
  EXTRACT(HOUR FROM e.metric_timestamp) AS hour_of_day,
  EXTRACT(DAYOFWEEK FROM e.metric_timestamp) AS day_of_week,
  EXTRACT(DAY FROM e.metric_timestamp) AS day_of_month,

  -- Missing hour indicator
  IF(f.metric_timestamp IS NULL, 1, 0) AS is_missing_hour

FROM expected_hours e
LEFT JOIN
  `sab-dev-dap-lakehouse-1470.data_quality.dq_feature` f
ON e.metric_timestamp = f.metric_timestamp;
