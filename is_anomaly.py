from typing import Any


def _is_positive(value: Any) -> bool:
    """
    Returns True when a DQ metric indicates a violation.

    Handles:
        1
        1.0
        > 0
        None
        NaN
    """
    if value is None:
        return False

    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _is_above_threshold(value: Any, threshold: float) -> bool:
    """
    Returns True when a numeric DQ ratio exceeds the configured threshold.
    """
    if value is None:
        return False

    try:
        return float(value) > threshold
    except (TypeError, ValueError):
        return False


def explain_anomaly(
    row,
    z_score_threshold: float = 3.0,
    null_rate_threshold: float = 0.05,
    duplicate_rate_threshold: float = 0.0,
):
    """
    Generate a human-readable explanation for an anomalous
    data-quality observation.

    Parameters
    ----------
    row:
        Pandas Series containing the ML/DQ features for one hour.

    z_score_threshold:
        Threshold used for statistical anomalies.

    null_rate_threshold:
        Threshold used for domain-level NULL ratios.

    duplicate_rate_threshold:
        Threshold used for duplicate-rate checks.

    Returns
    -------
    str
        Semicolon-separated explanation of detected anomaly causes.
    """

    reasons = []

    # ==========================================================
    # 1. Statistical anomalies
    # ==========================================================

    if _is_above_threshold(
        abs(row.get("row_count_score")),
        z_score_threshold
    ):
        reasons.append("Unusual row volume")

    if _is_above_threshold(
        abs(row.get("event_count_zscore")),
        z_score_threshold
    ):
        reasons.append("Unusual event volume")

    if _is_above_threshold(
        abs(row.get("active_pax_zscore")),
        z_score_threshold
    ):
        reasons.append("Unusual active passenger volume")

    if _is_above_threshold(
        abs(row.get("ingestion_latency_zscore")),
        z_score_threshold
    ):
        reasons.append("Unusual ingestion latency")

    if _is_above_threshold(
        abs(row.get("order_total_zscore")),
        z_score_threshold
    ):
        reasons.append("Unusual order total amount")

    # ==========================================================
    # 2. Domain-level completeness
    # ==========================================================

    if _is_above_threshold(
        row.get("root_fields_null_ratio"),
        null_rate_threshold
    ):
        reasons.append("High root-level NULL ratio")

    if _is_above_threshold(
        row.get("financial_fields_null_ratio"),
        null_rate_threshold
    ):
        reasons.append("High financial-field NULL ratio")

    if _is_above_threshold(
        row.get("item_fields_null_ratio"),
        null_rate_threshold
    ):
        reasons.append("High order-item NULL ratio")

    if _is_above_threshold(
        row.get("service_critical_fields_null_ratio"),
        null_rate_threshold
    ):
        reasons.append("High service-level NULL ratio")

    if _is_above_threshold(
        row.get("segment_fields_null_ratio"),
        null_rate_threshold
    ):
        reasons.append("High segment-level NULL ratio")

    if _is_above_threshold(
        row.get("payment_fields_null_ratio"),
        null_rate_threshold
    ):
        reasons.append("High payment-field NULL ratio")

    if _is_above_threshold(
        row.get("passenger_fields_null_ratio"),
        null_rate_threshold
    ):
        reasons.append("High passenger-field NULL ratio")

    # ==========================================================
    # 3. Duplicate checks
    # ==========================================================

    if _is_above_threshold(
        row.get("business_key_duplicate_rate"),
        duplicate_rate_threshold
    ):
        reasons.append("Business-key duplicates detected")

    if _is_above_threshold(
        row.get("event_id_duplicate_rate"),
        duplicate_rate_threshold
    ):
        reasons.append("Event ID duplicates detected")

    # ==========================================================
    # 4. Missing-hour anomaly
    # ==========================================================

    if _is_positive(row.get("is_missing_hour")):
        reasons.append("Missing hourly data")

    # ==========================================================
    # 5. Structural anomalies
    # ==========================================================

    if _is_positive(row.get("flag_missing_all_items")):
        reasons.append("All order items are missing")

    if _is_positive(row.get("flag_missing_all_passengers")):
        reasons.append("All passengers are missing")

    if _is_positive(row.get("flag_missing_all_services")):
        reasons.append("All services are missing")

    # ==========================================================
    # 6. Conditional/business-rule violations
    # ==========================================================

    if _is_positive(row.get("flag_paid_but_missing_amt")):
        reasons.append(
            "Paid order is missing total amount"
        )

    if _is_positive(row.get("flag_paid_but_missing_ccy")):
        reasons.append(
            "Paid order is missing total currency"
        )

    if _is_positive(row.get("flag_error_without_code")):
        reasons.append(
            "Order error is missing error code"
        )

    if _is_positive(row.get("flag_error_without_category")):
        reasons.append(
            "Order error is missing error category"
        )

    if _is_positive(row.get("flag_closed_missing_balance")):
        reasons.append(
            "Closed paid order is missing payment balance"
        )

    if _is_positive(row.get("flag_pax_without_trip_type")):
        reasons.append(
            "Passenger exists without trip type"
        )

    if _is_positive(row.get("flag_pax_without_trip_route")):
        reasons.append(
            "Passenger exists without trip route"
        )

    if _is_positive(row.get("flag_total_amt_without_ccy")):
        reasons.append(
            "Order total amount is missing currency"
        )

    if _is_positive(row.get("flag_base_amt_without_ccy")):
        reasons.append(
            "Order base amount is missing currency"
        )

    if _is_positive(row.get("flag_tax_amt_without_ccy")):
        reasons.append(
            "Order tax amount is missing currency"
        )

    if _is_positive(row.get("flag_active_pax_exceeds_total")):
        reasons.append(
            "Active passengers exceed total passengers"
        )

    if _is_positive(row.get("flag_paid_closed_no_payments")):
        reasons.append(
            "Closed paid order has no payment records"
        )

    # ==========================================================
    # 7. Order-item anomalies
    # ==========================================================

    if _is_positive(row.get("flag_cancelled_missing_reason")):
        reasons.append(
            "Cancelled order item is missing cancellation reason"
        )

    if _is_positive(row.get("flag_item_amt_without_ccy")):
        reasons.append(
            "Order-item amount is missing currency"
        )

    if _is_positive(row.get("flag_item_base_amt_without_ccy")):
        reasons.append(
            "Order-item base amount is missing currency"
        )

    # ==========================================================
    # 8. Service / flight anomalies
    # ==========================================================

    if _is_positive(row.get("flag_active_svc_missing_ticket")):
        reasons.append(
            "Active/closed service is missing ticket number"
        )

    if _is_positive(row.get("flag_flight_missing_times")):
        reasons.append(
            "Flight service is missing segment times"
        )

    if _is_positive(row.get("flag_flight_missing_legs")):
        reasons.append(
            "Flight service is missing legs"
        )

    # ==========================================================
    # 9. Payment anomalies
    # ==========================================================

    if _is_positive(row.get("flag_pay_amt_without_ccy")):
        reasons.append(
            "Payment amount is missing currency"
        )

    # ==========================================================
    # 10. Fallback
    # ==========================================================

    if not reasons:
        reasons.append(
            "Isolation Forest detected an unusual data-quality pattern"
        )

    return "; ".join(reasons)
