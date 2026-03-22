# Migration Guide

This guide helps teams moving to Northwind Cloud from existing analytics platforms. We support migrations from Tableau, Looker, Metabase, Mode, and homegrown solutions.

## Pre-migration checklist

Before starting:
- Inventory existing dashboards (URL, owner, last viewed, business criticality)
- Identify top 10 most-used dashboards — start with these
- List data sources and connection credentials
- Plan a freeze period for legacy platform changes (typically 2 weeks)
- Communicate the migration timeline to all dashboard consumers

## From Tableau

### What transfers cleanly
- SQL queries and data models (export from Tableau, paste into Northwind)
- Calculated fields (most syntax is similar)
- Standard chart types (bar, line, scatter, pie, table)
- Filters and parameters

### What requires manual rework
- Tableau-specific features: sets, bins, table calculations
- Custom Tableau extensions (no equivalent)
- LOD expressions (require rewriting in SQL)
- Story / dashboard actions (use Northwind's drill-down instead)

### Tooling
- Use `nw-tableau-importer` CLI to bulk-import .twbx files (best-effort, manual review needed)
- Available at github.com/northwind/migration-tools

## From Looker

### What transfers
- LookML model files can be imported as data source definitions
- Explores map to Northwind data sources
- Most Looker visualizations have direct equivalents

### What requires manual rework
- Liquid templating must be rewritten in our SQL templating syntax
- Persisted derived tables: rebuild as Northwind scheduled materialized views
- Looker actions: replicate using Northwind webhooks or reverse ETL

## From Metabase

Migration is straightforward — both products use SQL queries with similar visualization layers. The Metabase JSON export can be parsed and re-imported via our API.

Steps:
1. Export Metabase questions and dashboards as JSON (Settings → Export)
2. Run `nw-metabase-importer dump.json --workspace ws_xyz`
3. Manually verify dashboards load correctly

About 80% of Metabase content imports automatically.

## From homegrown / SQL files

If your "current platform" is a folder of SQL files plus screenshots:
1. Bulk-import SQL files via `nw-cli sql import ./queries`
2. Each file becomes a saved query, organized by folder
3. Build dashboards on top of queries in the UI

## Post-migration

### Validation
- Compare 5-10 critical dashboards side-by-side for 1 week
- Confirm aggregated numbers match (within rounding)
- Investigate any discrepancies — usually GROUP BY or filter differences

### Cutover
- Update DNS / bookmark links to new dashboards
- Add a deprecation banner on legacy dashboards 30 days before retirement
- Archive (don't delete) old dashboards for 90 days as fallback

### Training
- Week 1 post-migration: extra office hours for questions
- Record 30-min screencast on common workflows
- Document any custom internal patterns (e.g., naming conventions)

## Migration assistance

Enterprise customers receive dedicated migration assistance from their assigned engineer. Business plan customers can purchase a one-time professional services engagement starting at $5,000.

For self-service migration, our partner network includes certified consultants — see partners.northwind.cloud for the directory.
