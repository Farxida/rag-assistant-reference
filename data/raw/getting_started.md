# Getting Started

This guide walks through setting up your first Northwind Cloud workspace and connecting your first data source. Total time: about 15 minutes.

## Step 1 — Create a workspace

1. Sign up at app.northwind.cloud with your work email
2. Verify your email via the link sent to your inbox (delivery takes 1–2 minutes)
3. Choose a workspace name and region (cannot be changed after creation)
4. Invite teammates by email (optional, can be done later)

The free plan gives you 14 days to evaluate paid features. After 14 days, the workspace reverts to Free tier limits unless upgraded.

## Step 2 — Connect a data source

Northwind supports 60+ connectors. Most common path:

1. Go to **Data → Connections → Add new**
2. Select your source (PostgreSQL, MySQL, Snowflake, etc.)
3. Provide connection credentials. We recommend creating a read-only user on your database.
4. Test the connection — should succeed within 10 seconds
5. Select tables to sync and choose a refresh schedule (15min, 1h, 6h, daily)

For files (CSV, JSON, Parquet), use **Data → Upload** and drag-and-drop. Files up to 10 GB are supported.

## Step 3 — Build your first dashboard

1. Go to **Dashboards → New dashboard**
2. Click **Add chart** and select a data source from Step 2
3. Use the visual query builder or write SQL directly
4. Choose a chart type (bar, line, table, etc.)
5. Apply filters, group-by, and aggregations as needed
6. Save and share with teammates via the share button

## Step 4 — Set up scheduled reports (optional)

1. Open any dashboard
2. Click **Schedule → New schedule**
3. Choose recipients (email addresses or Slack channels)
4. Set frequency (daily, weekly, monthly)
5. Optionally restrict to filtered views

## Common first-time issues

- **Connection failed: timeout** — check that your database allows connections from Northwind IP ranges (listed in **Settings → Network**)
- **Empty tables** — verify the read-only user has SELECT permissions on the schema
- **Slow first sync** — initial sync can take longer than incremental syncs; subsequent updates are typically under 1 minute
