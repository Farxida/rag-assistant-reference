# Integrations

Northwind Cloud integrates with the tools your team already uses. Integrations are organized into three categories: data sources, output destinations, and operational tools.

## Data sources (60+ connectors)

### Databases
PostgreSQL, MySQL, SQL Server, Oracle, MongoDB, DynamoDB, Cassandra, Redis, ClickHouse

### Cloud data warehouses
Snowflake, BigQuery, Redshift, Databricks, Azure Synapse

### Cloud storage
AWS S3, Google Cloud Storage, Azure Blob Storage

### SaaS applications
- **CRM**: Salesforce, HubSpot, Pipedrive, Zoho
- **Marketing**: Marketo, Mailchimp, ActiveCampaign, Klaviyo
- **Product analytics**: Mixpanel, Amplitude, Segment
- **Payments**: Stripe, Braintree, Adyen
- **Support**: Zendesk, Intercom, Freshdesk

### Streaming
Apache Kafka, AWS Kinesis, Google Pub/Sub

## Output destinations

- **Slack**: scheduled reports, alerts, dashboard links
- **Microsoft Teams**: same as Slack
- **Email**: scheduled PDF or PNG exports
- **Webhooks**: any HTTP endpoint
- **Reverse ETL**: write transformed data back to Salesforce, HubSpot, or any database

## Operational tools

### Identity providers (SSO)
Okta, Azure AD, Google Workspace, OneLogin, Auth0, generic SAML 2.0

### Monitoring
Datadog (metrics export), PagerDuty (alert routing), Opsgenie

### Version control
GitHub, GitLab — sync dashboards as code via the `nw-cli` tool

## Custom integrations

If your tool is not on the list, you can:

1. Use the **Generic JDBC connector** for any database with a JDBC driver
2. Use the **HTTP Pull connector** for any REST API returning JSON
3. Write a custom Python connector using the SDK at github.com/northwind/connector-sdk
