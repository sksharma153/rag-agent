-- ============================================================
-- dq_feature.sql
-- Integrated Data Quality feature aggregation for order_history
--
-- Source:
--   sab-dev-dap-lakehouse-1470.dw_order.order_history
--
-- Target:
--   sab-dev-dap-lakehouse-1470.data_quality.dq_feature
--
-- The detailed DQ rules below are based on the sample SQL/screenshots
-- provided for this project, while retaining the original hourly
-- volume, uniqueness, amount and ingestion-latency metrics.
-- ============================================================

CREATE OR REPLACE TABLE
  `sab-dev-dap-lakehouse-1470.data_quality.dq_feature`
PARTITION BY DATE(metric_timestamp)
CLUSTER BY table_name
AS

WITH order_history AS (
  SELECT
    TIMESTAMP_TRUNC(event_ts, HOUR) AS metric_timestamp,

    -- Identifiers / tracing
    order_id,
    order_version,
    event_id,
    event_ts,
    dh_job_id,
    dh_ingestion_ts,

    -- Root-level fields
    order_type_cd,
    order_status,
    order_change_actions,
    last_update_event_ts,
    create_audit_event_ts,
    request_ts,
    response_ts,
    trip_type_cd,
    trip_origin_airport_cd,
    trip_destination_airport_cd,
    create_channel_cd,
    last_update_channel_cd,
    pos_channel_cd,
    pos_country_cd,
    active_pax_in_order,
    total_pax_in_order,
    paid_order_flag,
    migration_flag,
    source,
    retailer_order_id,
    retailer_owner_cd,
    order_error_flag,
    error_cd,
    error_category,

    -- Financial fields
    order_total_amt,
    order_total_ccy,
    order_base_amt,
    order_base_ccy,
    order_total_tax_amt,
    order_total_tax_ccy,
    order_discount_amt,
    order_discount_ccy,
    order_base_equivalent_amt,
    order_base_equivalent_ccy,
    order_payment_balance,
    order_payment_balance_ccy,
    order_forfeited_total_amt,
    order_forfeited_total_ccy,

    -- Nested arrays
    order_item_details,
    payment_details,
    passenger_details,
    price_class_details,
    distribution_chain_link,

    -- Existing amount metrics
    loyalty_unit_amt,
    monetary_total_amt,
    sequence_number

  FROM
    `sab-dev-dap-lakehouse-1470.dw_order.order_history`
  WHERE
    event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
),

base_metrics AS (
  SELECT
    'order_history' AS table_name,
    metric_timestamp,

    -- ==========================================================
    -- Existing volume metrics
    -- ==========================================================
    COUNT(*) AS row_count,
    COUNT(DISTINCT order_id) AS distinct_order_count,
    COUNT(DISTINCT event_id) AS distinct_event_count,

    -- ==========================================================
    -- Existing completeness metrics
    -- ==========================================================
    SAFE_DIVIDE(COUNTIF(order_id IS NULL), COUNT(*))
      AS order_id_null_rate,
    SAFE_DIVIDE(COUNTIF(order_version IS NULL), COUNT(*))
      AS order_version_null_rate,
    SAFE_DIVIDE(COUNTIF(event_id IS NULL), COUNT(*))
      AS event_id_null_rate,
    SAFE_DIVIDE(COUNTIF(order_type_cd IS NULL), COUNT(*))
      AS order_type_null_rate,
    SAFE_DIVIDE(COUNTIF(order_status IS NULL), COUNT(*))
      AS order_status_null_rate,

    -- ==========================================================
    -- Existing uniqueness metrics
    -- ==========================================================
    SAFE_DIVIDE(
      COUNT(*) - COUNT(DISTINCT STRUCT(order_id, order_version)),
      COUNT(*)
    ) AS business_key_duplicate_rate,

    SAFE_DIVIDE(
      COUNT(*) - COUNT(DISTINCT event_id),
      COUNT(*)
    ) AS event_id_duplicate_rate,

    -- ==========================================================
    -- Existing passenger metrics
    -- ==========================================================
    AVG(active_pax_in_order) AS active_pax_avg,
    STDDEV(active_pax_in_order) AS active_pax_stddev,
    MIN(active_pax_in_order) AS active_pax_min,
    MAX(active_pax_in_order) AS active_pax_max,
    APPROX_QUANTILES(active_pax_in_order, 100)[OFFSET(50)]
      AS active_pax_p50,
    APPROX_QUANTILES(active_pax_in_order, 100)[OFFSET(95)]
      AS active_pax_p95,
    APPROX_QUANTILES(active_pax_in_order, 100)[OFFSET(99)]
      AS active_pax_p99,

    -- ==========================================================
    -- Existing order amount metrics
    -- ==========================================================
    AVG(order_total_amt) AS order_total_avg,
    STDDEV(order_total_amt) AS order_total_stddev,
    MIN(order_total_amt) AS order_total_min,
    MAX(order_total_amt) AS order_total_max,
    APPROX_QUANTILES(order_total_amt, 100)[OFFSET(50)]
      AS order_total_p50,
    APPROX_QUANTILES(order_total_amt, 100)[OFFSET(95)]
      AS order_total_p95,
    APPROX_QUANTILES(order_total_amt, 100)[OFFSET(99)]
      AS order_total_p99,

    SAFE_DIVIDE(COUNTIF(order_total_amt < 0), COUNT(*))
      AS negative_order_total_rate,
    SAFE_DIVIDE(COUNTIF(order_discount_amt < 0), COUNT(*))
      AS negative_discount_rate,

    -- ==========================================================
    -- Existing timestamp / latency metrics
    -- ==========================================================
    SAFE_DIVIDE(
      COUNTIF(event_ts > CURRENT_TIMESTAMP()),
      COUNT(*)
    ) AS future_event_rate,

    SAFE_DIVIDE(
      COUNTIF(dh_ingestion_ts < event_ts),
      COUNT(*)
    ) AS invalid_ingestion_timestamp_rate,

    AVG(
      TIMESTAMP_DIFF(dh_ingestion_ts, event_ts, SECOND)
    ) AS avg_ingestion_latency_seconds,

    APPROX_QUANTILES(
      TIMESTAMP_DIFF(dh_ingestion_ts, event_ts, SECOND), 100
    )[OFFSET(95)] AS ingestion_latency_p95,

    APPROX_QUANTILES(
      TIMESTAMP_DIFF(dh_ingestion_ts, event_ts, SECOND), 100
    )[OFFSET(99)] AS ingestion_latency_p99,

    -- ==========================================================
    -- FEATURE SET 1: Root-level NULL indicators
    -- ==========================================================
    COUNTIF(order_id IS NULL) AS null_order_id,
    COUNTIF(order_version IS NULL) AS null_order_version,
    COUNTIF(order_type_cd IS NULL) AS null_order_type_cd,
    COUNTIF(order_status IS NULL) AS null_order_status,
    COUNTIF(order_change_actions IS NULL) AS null_order_change_actions,
    COUNTIF(event_id IS NULL) AS null_event_id,
    COUNTIF(event_ts IS NULL) AS null_event_ts,
    COUNTIF(last_update_event_ts IS NULL) AS null_last_update_event_ts,
    COUNTIF(create_audit_event_ts IS NULL) AS null_create_audit_event_ts,
    COUNTIF(request_ts IS NULL) AS null_request_ts,
    COUNTIF(response_ts IS NULL) AS null_response_ts,
    COUNTIF(trip_type_cd IS NULL) AS null_trip_type_cd,
    COUNTIF(trip_origin_airport_cd IS NULL) AS null_trip_origin_airport_cd,
    COUNTIF(trip_destination_airport_cd IS NULL)
      AS null_trip_destination_airport_cd,
    COUNTIF(create_channel_cd IS NULL) AS null_create_channel_cd,
    COUNTIF(last_update_channel_cd IS NULL)
      AS null_last_update_channel_cd,
    COUNTIF(pos_channel_cd IS NULL) AS null_pos_channel_cd,
    COUNTIF(pos_country_cd IS NULL) AS null_pos_country_cd,
    COUNTIF(active_pax_in_order IS NULL) AS null_active_pax_in_order,
    COUNTIF(total_pax_in_order IS NULL) AS null_total_pax_in_order,
    COUNTIF(paid_order_flag IS NULL) AS null_paid_order_flag,
    COUNTIF(migration_flag IS NULL) AS null_migration_flag,
    COUNTIF(source IS NULL) AS null_source,
    COUNTIF(retailer_order_id IS NULL) AS null_retailer_order_id,
    COUNTIF(retailer_owner_cd IS NULL) AS null_retailer_owner_cd,

    -- ==========================================================
    -- FEATURE SET 2: Financial completeness
    -- ==========================================================
    COUNTIF(order_total_amt IS NULL) AS null_order_total_amt,
    COUNTIF(order_total_ccy IS NULL) AS null_order_total_ccy,
    COUNTIF(order_base_amt IS NULL) AS null_order_base_amt,
    COUNTIF(order_base_ccy IS NULL) AS null_order_base_ccy,
    COUNTIF(order_total_tax_amt IS NULL) AS null_order_total_tax_amt,
    COUNTIF(order_total_tax_ccy IS NULL) AS null_order_total_tax_ccy,
    COUNTIF(order_discount_amt IS NULL) AS null_order_discount_amt,
    COUNTIF(order_discount_ccy IS NULL) AS null_order_discount_ccy,
    COUNTIF(order_base_equivalent_amt IS NULL)
      AS null_order_base_equivalent_amt,
    COUNTIF(order_base_equivalent_ccy IS NULL)
      AS null_order_base_equivalent_ccy,
    COUNTIF(order_payment_balance IS NULL) AS null_order_payment_balance,
    COUNTIF(order_payment_balance_ccy IS NULL)
      AS null_order_payment_balance_ccy,
    COUNTIF(order_forfeited_total_amt IS NULL)
      AS null_order_forfeited_total_amt,
    COUNTIF(order_forfeited_total_ccy IS NULL)
      AS null_order_forfeited_total_ccy,

    -- ==========================================================
    -- FEATURE SET 3: Conditional / business-rule violations
    -- ==========================================================
    COUNTIF(
      paid_order_flag = TRUE AND order_total_amt IS NULL
    ) AS flag_paid_but_missing_amt,

    COUNTIF(
      paid_order_flag = TRUE AND order_total_ccy IS NULL
    ) AS flag_paid_but_missing_ccy,

    COUNTIF(
      order_error_flag = TRUE AND error_cd IS NULL
    ) AS flag_error_without_code,

    COUNTIF(
      order_error_flag = TRUE AND error_category IS NULL
    ) AS flag_error_without_category,

    COUNTIF(
      order_status = 'ORDER_STATUS_CLOSED'
      AND order_payment_balance IS NULL
    ) AS flag_closed_missing_balance,

    COUNTIF(
      total_pax_in_order > 0 AND trip_type_cd IS NULL
    ) AS flag_pax_without_trip_type,

    COUNTIF(
      total_pax_in_order > 0
      AND (
        trip_origin_airport_cd IS NULL
        OR trip_destination_airport_cd IS NULL
      )
    ) AS flag_pax_without_trip_route,

    COUNTIF(
      order_total_amt IS NOT NULL
      AND order_total_ccy IS NULL
    ) AS flag_total_amt_without_ccy,

    COUNTIF(
      order_base_amt IS NOT NULL
      AND order_base_ccy IS NULL
    ) AS flag_base_amt_without_ccy,

    COUNTIF(
      order_total_tax_amt IS NOT NULL
      AND order_total_tax_ccy IS NULL
    ) AS flag_tax_amt_without_ccy,

    COUNTIF(
      active_pax_in_order > total_pax_in_order
    ) AS flag_active_pax_exceeds_total,

    COUNTIF(
      order_status = 'ORDER_STATUS_CLOSED'
      AND paid_order_flag = TRUE
      AND ARRAY_LENGTH(payment_details) = 0
    ) AS flag_paid_closed_no_payments,

    -- ==========================================================
    -- FEATURE SET 4: Structural array counts
    -- ==========================================================
    SUM(COALESCE(ARRAY_LENGTH(order_item_details), 0))
      AS total_order_items,

    SUM(COALESCE(ARRAY_LENGTH(payment_details), 0))
      AS total_payments,

    SUM(COALESCE(ARRAY_LENGTH(passenger_details), 0))
      AS total_passengers,

    SUM(COALESCE(ARRAY_LENGTH(order_change_actions), 0))
      AS change_action_count,

    SUM(COALESCE(ARRAY_LENGTH(price_class_details), 0))
      AS price_class_count,

    SUM(COALESCE(ARRAY_LENGTH(distribution_chain_link), 0))
      AS distribution_chain_count,

    SUM(
      CASE
        WHEN ARRAY_LENGTH(order_item_details) IS NULL
          OR ARRAY_LENGTH(order_item_details) = 0
        THEN 1 ELSE 0
      END
    ) AS flag_missing_all_items,

    SUM(
      CASE
        WHEN ARRAY_LENGTH(passenger_details) IS NULL
          OR ARRAY_LENGTH(passenger_details) = 0
        THEN 1 ELSE 0
      END
    ) AS flag_missing_all_passengers,

    SUM(
      CASE
        WHEN ARRAY_LENGTH(order_item_details) IS NULL
          OR ARRAY_LENGTH(order_item_details) = 0
        THEN 1 ELSE 0
      END
    ) AS flag_missing_all_services_base

  FROM order_history
  GROUP BY metric_timestamp
),

item_metrics AS (
  SELECT
    metric_timestamp,

    -- Item-level NULLs
    COUNTIF(item.order_item_id IS NULL) AS null_item_ids,
    COUNTIF(item.order_item_status IS NULL) AS null_item_statuses,
    COUNTIF(item.order_item_total_amt IS NULL) AS null_item_total_amts,
    COUNTIF(item.order_item_total_ccy IS NULL) AS null_item_total_ccys,
    COUNTIF(item.order_item_base_amt IS NULL) AS null_item_base_amts,
    COUNTIF(item.order_item_channel IS NULL) AS null_item_channels,

    -- Item-level rules
    COUNTIF(
      item.order_item_status = 'CANCELLED'
      AND item.order_item_cancel_reason IS NULL
    ) AS flag_cancelled_missing_reason,

    COUNTIF(
      item.order_item_total_amt IS NOT NULL
      AND item.order_item_total_ccy IS NULL
    ) AS flag_item_amt_without_ccy,

    COUNTIF(
      item.order_item_base_amt IS NOT NULL
      AND item.order_item_base_ccy IS NULL
    ) AS flag_item_base_amt_without_ccy,

    -- Service-level counts / NULL indicators
    SUM(COALESCE(ARRAY_LENGTH(item.service_details), 0))
      AS total_service_count,

    SUM((
      SELECT COUNTIF(svc.ticket_number IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_ticket_numbers,

    SUM((
      SELECT COUNTIF(svc.fare_basis_cd IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_fare_basis_codes,

    SUM((
      SELECT COUNTIF(svc.journey_departure_dt IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_journey_departure_dts,

    SUM((
      SELECT COUNTIF(svc.journey_arrival_dt IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_journey_arrival_dts,

    SUM((
      SELECT COUNTIF(svc.segment_origin_airport_cd IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_segment_origins,

    SUM((
      SELECT COUNTIF(svc.segment_destination_airport_cd IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_segment_destinations,

    SUM((
      SELECT COUNTIF(svc.segment_departure_dt IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_segment_departure_dts,

    SUM((
      SELECT COUNTIF(svc.segment_arrival_dt IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_segment_arrival_dts,

    SUM((
      SELECT COUNTIF(svc.marketing_carrier_cd IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_marketing_carrier_cds,

    SUM((
      SELECT COUNTIF(svc.operating_carrier_cd IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_operating_carrier_cds,

    SUM((
      SELECT COUNTIF(svc.booking_class_cd IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_booking_class_cds,

    SUM((
      SELECT COUNTIF(svc.cabin_cd IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_cabin_cds,

    SUM((
      SELECT COUNTIF(svc.passenger_id IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_passenger_ids_in_svc,

    SUM((
      SELECT COUNTIF(svc.service_id IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_service_ids,

    SUM((
      SELECT COUNTIF(svc.service_status IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_service_statuses,

    SUM((
      SELECT COUNTIF(svc.journey_id IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_journey_ids,

    SUM((
      SELECT COUNTIF(svc.segment_id IS NULL)
      FROM UNNEST(item.service_details) AS svc
    )) AS null_segment_ids,

    -- Active/closed service without ticket
    SUM((
      SELECT COUNTIF(svc.ticket_number IS NULL)
      FROM UNNEST(item.service_details) AS svc
      WHERE item.order_item_status IN ('ACTIVE', 'CLOSED')
    )) AS flag_active_svc_missing_ticket,

    -- Flight service rules
    SUM((
      SELECT COUNTIF(
        svc.segment_departure_dt IS NULL
        OR svc.segment_arrival_dt IS NULL
      )
      FROM UNNEST(item.service_details) AS svc
      WHERE svc.service_type = 'FLIGHT'
    )) AS flag_flight_missing_times,

    SUM((
      SELECT COUNTIF(
        ARRAY_LENGTH(svc.leg_details) IS NULL
        OR ARRAY_LENGTH(svc.leg_details) = 0
      )
      FROM UNNEST(item.service_details) AS svc
      WHERE svc.service_type = 'FLIGHT'
    )) AS flag_flight_missing_legs

  FROM order_history
  CROSS JOIN UNNEST(order_item_details) AS item
  GROUP BY metric_timestamp
),

payment_metrics AS (
  SELECT
    metric_timestamp,

    COUNTIF(pay.payment_id IS NULL) AS null_payment_ids,
    COUNTIF(pay.payment_status IS NULL) AS null_payment_statuses,
    COUNTIF(pay.payment_method IS NULL) AS null_payment_methods,
    COUNTIF(pay.payment_amt IS NULL) AS null_payment_amts,
    COUNTIF(pay.payment_ccy IS NULL) AS null_payment_ccys,
    COUNTIF(pay.payment_timestamp IS NULL) AS null_payment_timestamps,

    COUNTIF(
      pay.payment_amt IS NOT NULL
      AND pay.payment_ccy IS NULL
    ) AS flag_pay_amt_without_ccy

  FROM order_history
  CROSS JOIN UNNEST(payment_details) AS pay
  GROUP BY metric_timestamp
),

passenger_metrics AS (
  SELECT
    metric_timestamp,

    COUNTIF(pax.passenger_id IS NULL) AS null_pax_ids,
    COUNTIF(pax.pax_ptc_cd IS NULL) AS null_pax_ptc_cds,
    COUNTIF(pax.pax_first_name IS NULL) AS null_pax_first_names,
    COUNTIF(pax.pax_last_name IS NULL) AS null_pax_last_names

  FROM order_history
  CROSS JOIN UNNEST(passenger_details) AS pax
  GROUP BY metric_timestamp
),

combined AS (
  SELECT
    b.*,

    -- Item / service
    COALESCE(i.total_service_count, 0) AS total_services,
    COALESCE(i.null_item_ids, 0) AS null_item_ids,
    COALESCE(i.null_item_statuses, 0) AS null_item_statuses,
    COALESCE(i.null_item_total_amts, 0) AS null_item_total_amts,
    COALESCE(i.null_item_total_ccys, 0) AS null_item_total_ccys,
    COALESCE(i.null_item_base_amts, 0) AS null_item_base_amts,
    COALESCE(i.null_item_channels, 0) AS null_item_channels,
    COALESCE(i.flag_cancelled_missing_reason, 0)
      AS flag_cancelled_missing_reason,
    COALESCE(i.flag_item_amt_without_ccy, 0)
      AS flag_item_amt_without_ccy,
    COALESCE(i.flag_item_base_amt_without_ccy, 0)
      AS flag_item_base_amt_without_ccy,

    COALESCE(i.null_ticket_numbers, 0) AS null_ticket_numbers,
    COALESCE(i.null_fare_basis_codes, 0) AS null_fare_basis_codes,
    COALESCE(i.null_journey_departure_dts, 0)
      AS null_journey_departure_dts,
    COALESCE(i.null_journey_arrival_dts, 0)
      AS null_journey_arrival_dts,
    COALESCE(i.null_segment_origins, 0) AS null_segment_origins,
    COALESCE(i.null_segment_destinations, 0)
      AS null_segment_destinations,
    COALESCE(i.null_segment_departure_dts, 0)
      AS null_segment_departure_dts,
    COALESCE(i.null_segment_arrival_dts, 0)
      AS null_segment_arrival_dts,
    COALESCE(i.null_marketing_carrier_cds, 0)
      AS null_marketing_carrier_cds,
    COALESCE(i.null_operating_carrier_cds, 0)
      AS null_operating_carrier_cds,
    COALESCE(i.null_booking_class_cds, 0)
      AS null_booking_class_cds,
    COALESCE(i.null_cabin_cds, 0) AS null_cabin_cds,
    COALESCE(i.null_passenger_ids_in_svc, 0)
      AS null_passenger_ids_in_svc,
    COALESCE(i.null_service_ids, 0) AS null_service_ids,
    COALESCE(i.null_service_statuses, 0) AS null_service_statuses,
    COALESCE(i.null_journey_ids, 0) AS null_journey_ids,
    COALESCE(i.null_segment_ids, 0) AS null_segment_ids,
    COALESCE(i.flag_active_svc_missing_ticket, 0)
      AS flag_active_svc_missing_ticket,
    COALESCE(i.flag_flight_missing_times, 0)
      AS flag_flight_missing_times,
    COALESCE(i.flag_flight_missing_legs, 0)
      AS flag_flight_missing_legs,

    -- Payment
    COALESCE(p.null_payment_ids, 0) AS null_payment_ids,
    COALESCE(p.null_payment_statuses, 0) AS null_payment_statuses,
    COALESCE(p.null_payment_methods, 0) AS null_payment_methods,
    COALESCE(p.null_payment_amts, 0) AS null_payment_amts,
    COALESCE(p.null_payment_ccys, 0) AS null_payment_ccys,
    COALESCE(p.null_payment_timestamps, 0) AS null_payment_timestamps,
    COALESCE(p.flag_pay_amt_without_ccy, 0)
      AS flag_pay_amt_without_ccy,

    -- Passenger
    COALESCE(x.null_pax_ids, 0) AS null_pax_ids,
    COALESCE(x.null_pax_ptc_cds, 0) AS null_pax_ptc_cds,
    COALESCE(x.null_pax_first_names, 0) AS null_pax_first_names,
    COALESCE(x.null_pax_last_names, 0) AS null_pax_last_names

  FROM base_metrics b
  LEFT JOIN item_metrics i
    USING (metric_timestamp)
  LEFT JOIN payment_metrics p
    USING (metric_timestamp)
  LEFT JOIN passenger_metrics x
    USING (metric_timestamp)
)

SELECT
  c.*,

  -- ============================================================
  -- FEATURE SET 9: Domain-level completeness / violation ratios
  -- ============================================================

  SAFE_DIVIDE(
      null_order_id
    + null_order_version
    + null_order_type_cd
    + null_order_status
    + null_order_change_actions
    + null_event_id
    + null_event_ts
    + null_last_update_event_ts
    + null_create_audit_event_ts
    + null_request_ts
    + null_response_ts
    + null_trip_type_cd
    + null_trip_origin_airport_cd
    + null_trip_destination_airport_cd
    + null_create_channel_cd
    + null_last_update_channel_cd
    + null_pos_channel_cd
    + null_pos_country_cd
    + null_active_pax_in_order
    + null_total_pax_in_order
    + null_paid_order_flag
    + null_migration_flag
    + null_source
    + null_retailer_order_id
    + null_retailer_owner_cd,
    row_count * 25
  ) AS root_fields_null_ratio,

  SAFE_DIVIDE(
      null_order_total_amt
    + null_order_total_ccy
    + null_order_base_amt
    + null_order_base_ccy
    + null_order_total_tax_amt
    + null_order_total_tax_ccy
    + null_order_discount_amt
    + null_order_discount_ccy
    + null_order_base_equivalent_amt
    + null_order_base_equivalent_ccy
    + null_order_payment_balance
    + null_order_payment_balance_ccy
    + null_order_forfeited_total_amt
    + null_order_forfeited_total_ccy,
    row_count * 14
  ) AS financial_fields_null_ratio,

  SAFE_DIVIDE(
      flag_paid_but_missing_amt
    + flag_paid_but_missing_ccy
    + flag_error_without_code
    + flag_error_without_category
    + flag_closed_missing_balance
    + flag_pax_without_trip_type
    + flag_pax_without_trip_route
    + flag_total_amt_without_ccy
    + flag_base_amt_without_ccy
    + flag_tax_amt_without_ccy
    + flag_active_pax_exceeds_total
    + flag_paid_closed_no_payments,
    row_count * 12
  ) AS conditional_violation_ratio,

  SAFE_DIVIDE(
      null_item_ids
    + null_item_statuses
    + null_item_total_amts
    + null_item_channels,
    total_order_items * 4
  ) AS item_fields_null_ratio,

  SAFE_DIVIDE(
      null_ticket_numbers
    + null_fare_basis_codes
    + null_journey_departure_dts
    + null_segment_origins
    + null_marketing_carrier_cds
    + null_booking_class_cds,
    total_services * 6
  ) AS service_critical_fields_null_ratio,

  SAFE_DIVIDE(
      null_segment_departure_dts
    + null_segment_arrival_dts
    + null_segment_origins
    + null_segment_destinations
    + null_segment_ids,
    total_services * 5
  ) AS segment_fields_null_ratio,

  SAFE_DIVIDE(
      null_payment_ids
    + null_payment_statuses
    + null_payment_methods
    + null_payment_amts
    + null_payment_ccys,
    total_payments * 5
  ) AS payment_fields_null_ratio,

  SAFE_DIVIDE(
      null_pax_ids
    + null_pax_ptc_cds
    + null_pax_first_names
    + null_pax_last_names,
    total_passengers * 4
  ) AS passenger_fields_null_ratio,

  -- ============================================================
  -- FEATURE SET 10: Total conditional violations
  -- ============================================================
    flag_paid_but_missing_amt
  + flag_paid_but_missing_ccy
  + flag_error_without_code
  + flag_error_without_category
  + flag_closed_missing_balance
  + flag_pax_without_trip_type
  + flag_pax_without_trip_route
  + flag_total_amt_without_ccy
  + flag_base_amt_without_ccy
  + flag_tax_amt_without_ccy
  + flag_active_pax_exceeds_total
  + flag_paid_closed_no_payments
  + COALESCE(flag_cancelled_missing_reason, 0)
  + COALESCE(flag_item_amt_without_ccy, 0)
  + COALESCE(flag_item_base_amt_without_ccy, 0)
  + COALESCE(flag_active_svc_missing_ticket, 0)
  + COALESCE(flag_flight_missing_times, 0)
  + COALESCE(flag_flight_missing_legs, 0)
  + COALESCE(flag_pay_amt_without_ccy, 0)
    AS total_conditional_violations

FROM combined AS c;
