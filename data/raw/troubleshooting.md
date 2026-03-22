# Troubleshooting

Common issues and how to fix them. If your problem isn't listed here, contact support@northwind.cloud.

## Connection issues

### "Connection failed: timeout"
- Verify Northwind IP ranges are allowed in your firewall (listed in **Settings → Network**)
- Check the database accepts external connections (often disabled by default in cloud providers)
- For VPC peering customers: confirm the peering connection is in `active` state

### "Authentication failed"
- Confirm credentials by connecting from your local machine first
- For SSL-required databases, ensure SSL mode is set to `require` or `verify-ca` in connection settings
- Some databases (Oracle, MS SQL) require a TNS / instance name in addition to the host

### "SSL handshake failed"
- Northwind enforces TLS 1.2 minimum. If your database is behind an old proxy, upgrade the proxy.
- For self-signed certificates, upload the CA cert in connection settings and select "verify-ca"

## Query and dashboard issues

### "Query timed out"
- Default timeout is 5 minutes. Increase to 30 minutes in **Settings → Query → Timeout**.
- For long-running queries, consider materializing intermediate results into a scheduled table.
- Add appropriate indexes to source tables (Northwind will warn if it detects a sequential scan over 1M rows)

### "Dashboard loading is slow"
- Check **Dashboard → Performance** — shows per-chart load times
- Enable **Auto-cache** on the dashboard to cache results for up to 24 hours
- Replace SELECT * with explicit column lists in underlying queries

### "Chart shows wrong numbers"
- Check that filters from the dashboard level haven't been overridden at the chart level
- Verify date ranges are interpreted in the dashboard timezone (default UTC, configurable per workspace)
- For aggregated metrics, confirm GROUP BY clauses match the chart's grouping

## Permission and access issues

### "I can't see a dashboard a teammate shared"
- Sharing is per-folder by default. Ask the teammate to verify folder permissions.
- Workspace admin can audit access via **Settings → Audit log**

### "API requests return 401"
- API keys can expire — check **Settings → API keys** for expiration date
- Confirm the key has appropriate scope (read vs write vs admin)
- Bearer prefix is required: `Authorization: Bearer nw_live_xxx`, not just the key

## Performance optimization

### Reducing query costs
- Use **Query → Cost preview** before running expensive queries
- Schedule heavy aggregations off-peak (we offer 50% discount on queries between 02:00-06:00 UTC on Business and above)
- Materialize repeated joins as scheduled views

### Reducing storage costs
- Enable auto-archival of cold data older than 90 days (compressed to 1/10th size)
- Drop unused dashboards and queries (dashboards over 6 months idle are flagged in **Settings → Cleanup**)

## Getting help

For support faster than email:
- Business plan: live chat in the bottom-right of the app, M-F 9am-6pm ET
- Enterprise: dedicated Slack channel with your assigned support engineer
- Status page: status.northwind.cloud (public)
