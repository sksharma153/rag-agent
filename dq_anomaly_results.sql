-- ============================================================
-- dq_anomaly_results.sql
-- Stores Isolation Forest anomaly results.
-- ============================================================

CREATE TABLE IF NOT EXISTS
  `sab-dev-dap-lakehouse-1470.data_quality.dq_anomaly_results`
(
  metric_timestamp TIMESTAMP NOT NULL,
  anomaly_score FLOAT64,
  is_anomaly BOOL NOT NULL,
  severity STRING,
  anomaly_reason STRING,
  model_version STRING,
  processed_at TIMESTAMP NOT NULL
)
PARTITION BY DATE(metric_timestamp)
CLUSTER BY severity, is_anomaly;
