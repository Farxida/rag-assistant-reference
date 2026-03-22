# Features

Northwind Cloud is a unified analytics platform that combines data warehousing, BI dashboards, and AI-driven insights for product teams.

## Core capabilities

### Data ingestion
- 60+ pre-built connectors: PostgreSQL, MySQL, MongoDB, Snowflake, BigQuery, Redshift, S3, GCS, Stripe, Salesforce, HubSpot, Segment
- Real-time streaming via Kafka and Kinesis
- CSV / JSON / Parquet file uploads up to 10 GB
- Custom Python and SQL transformations in scheduled pipelines

### Storage and compute
- Columnar storage with automatic compression
- Separation of compute and storage — pay only for active queries
- Auto-scaling query engine, no cluster sizing required
- Geographic regions: us-east-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-1

### Dashboards and visualizations
- 25+ chart types including geo-maps, funnels, cohort analysis, Sankey
- Interactive filters and drill-down on any chart
- Embedding via signed iframes for customer-facing dashboards
- Scheduled email and Slack reports
- Public sharing with read-only links

### AI and machine learning
- Natural-language to SQL via integrated LLM
- Forecasting (ARIMA, Prophet) on any metric
- Anomaly detection with configurable sensitivity
- Automated insight discovery on dashboards

### Collaboration
- Comments and threads on charts and dashboards
- Workspaces with role-based access control: Admin, Editor, Viewer
- Version history with one-click revert (last 90 days)
- Two-factor authentication required for Admin and Editor roles

## What's not included

Northwind does not provide ETL transformation infrastructure (use Fivetran or Airbyte upstream), customer data platforms (use Segment or Rudderstack), or operational alerting (use PagerDuty or Datadog).
