# API Reference

Northwind Cloud exposes a REST API for programmatic access to dashboards, queries, and data. The API is available on Starter plans and above.

## Authentication

All API requests require a Bearer token in the Authorization header:

```
Authorization: Bearer nw_live_<your_api_key>
```

API keys are created in **Settings → API keys**. Each key can be scoped to specific resources (read-only, write, admin) and given an expiry date.

## Base URL

```
https://api.northwind.cloud/v1
```

## Rate limits

| Plan | Requests per minute | Burst |
|------|---------------------|-------|
| Starter | 60 | 120 |
| Business | 600 | 1200 |
| Enterprise | Custom | Custom |

Exceeding the limit returns HTTP 429 with a `Retry-After` header.

## Core endpoints

### Run a query

```
POST /queries/run
{
  "sql": "SELECT count(*) FROM events WHERE date > '2024-01-01'",
  "data_source_id": "ds_abc123",
  "max_rows": 10000
}
```

Returns query results as JSON or, for large results, a signed URL to a Parquet file.

### List dashboards

```
GET /dashboards?workspace_id=ws_xyz789&limit=50
```

### Get dashboard data

```
GET /dashboards/{dashboard_id}/data
```

Returns all chart data for a dashboard in a single response.

### Trigger a sync

```
POST /connections/{connection_id}/sync
```

Manually triggers a data sync. Returns immediately with a job ID; check `/jobs/{job_id}` for status.

## SDKs

Official client libraries:
- Python: `pip install northwind-cloud`
- Node.js: `npm install @northwind/cloud`
- Go: `go get github.com/northwind/cloud-go`

## Webhooks

Northwind can POST to your endpoint when events occur (sync completed, query failed, alert triggered). Configure in **Settings → Webhooks**. Payload is signed with HMAC SHA-256; verify the `X-Northwind-Signature` header.
