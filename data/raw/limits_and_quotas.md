# Limits and Quotas

This page documents technical limits across plans. Limits are per workspace unless specified.

## User and access limits

| Limit | Free | Starter | Business | Enterprise |
|-------|------|---------|----------|------------|
| Users | 3 | 10 | 50 | Unlimited |
| Workspaces per organization | 1 | 3 | 10 | Unlimited |
| Concurrent SSO sessions | 1 | 5 | 25 | Unlimited |

## Storage limits

| Limit | Free | Starter | Business | Enterprise |
|-------|------|---------|----------|------------|
| Total data storage | 5 GB | 50 GB | 500 GB | Custom |
| Single file upload | 100 MB | 1 GB | 10 GB | 10 GB |
| Total dashboards | 50 | 500 | 5000 | Unlimited |
| Charts per dashboard | 20 | 50 | 100 | 200 |

## Query limits

| Limit | Free | Starter | Business | Enterprise |
|-------|------|---------|----------|------------|
| Queries per month | 10K | 100K | 1M | Custom |
| Query timeout | 1 min | 5 min | 30 min | 60 min |
| Result rows (inline) | 10K | 100K | 1M | 10M |
| Result rows (Parquet export) | 100K | 1M | 100M | Unlimited |
| Concurrent queries | 2 | 10 | 50 | Custom |

Excess queries on paid plans are billed at $0.0005 per query (you can set a hard cap).

## API rate limits

| Limit | Starter | Business | Enterprise |
|-------|---------|----------|------------|
| Requests per minute (per key) | 60 | 600 | Custom |
| Burst (per key) | 120 | 1200 | Custom |
| Requests per minute (per IP) | 600 | 6000 | Custom |

## Connection limits

| Limit | Free | Starter | Business | Enterprise |
|-------|------|---------|----------|------------|
| Active data sources | 1 | 5 | 50 | Unlimited |
| Sync frequency (minimum) | Daily | Hourly | 15 min | 1 min |
| Webhook endpoints | 1 | 10 | 100 | Unlimited |

## Embedding limits

For customer-facing embedded dashboards:

| Limit | Business | Enterprise |
|-------|----------|------------|
| Embedded views per month | 100K | Unlimited |
| Concurrent embed viewers | 100 | Unlimited |
| Custom CSS / branding | Yes | Yes + white-label |

## Other notable limits

- Maximum query response size: 100 MB inline (larger via Parquet)
- Maximum dashboard refresh frequency: 1 minute on Enterprise, 15 min on Business
- Maximum scheduled report frequency: every 15 minutes
- Maximum recipients per scheduled report: 50
- Audit log retention: 12 months (Business) / 7 years (Enterprise)
- Backup retention: 30 days (all paid plans)

## Hitting a limit

When you approach a limit:
- 80% threshold: email notification to workspace admins
- 95% threshold: email + in-app banner
- 100% threshold: graceful degradation (queue queries, throttle API) plus option to upgrade or pay overage

To request a custom limit increase, contact support@northwind.cloud with your use case.
