# Frequently Asked Questions

## General

**Q: What does Northwind Cloud do?**
A: It's a unified analytics platform combining data warehousing, BI dashboards, and AI-driven insights. Teams use it to consolidate data from multiple sources, build interactive dashboards, and surface insights automatically.

**Q: Who is it for?**
A: Product analytics, BI, and data teams at companies from 10 to 10,000 employees. Common roles: data analyst, analytics engineer, product manager, founder.

**Q: How does it compare to Looker / Tableau / Metabase?**
A: We focus on the full pipeline (ingestion + warehouse + dashboards + AI) in one product. Tableau and Looker are dashboard-only and require separate ETL and warehouse. Metabase is similar but lacks AI features and managed warehouse.

## Data and security

**Q: Where is my data stored?**
A: In the region you selected at workspace creation: us-east-1, us-west-2, eu-west-1, eu-central-1, or ap-southeast-1. Data does not leave the selected region.

**Q: Do you train AI models on customer data?**
A: No. We never use customer data to train shared models. Per-customer fine-tuning is available on Enterprise plan with explicit opt-in.

**Q: Can I bring my own encryption key?**
A: Yes, on Enterprise plan via AWS KMS, GCP Cloud KMS, or Azure Key Vault.

## Pricing and billing

**Q: Can I change plans mid-cycle?**
A: Yes. Upgrades are pro-rated to the day. Downgrades take effect at next renewal.

**Q: Do you offer discounts?**
A: 20% discount for annual billing. Educational and non-profit discounts available — contact sales. Startup program offers 50% off Business plan for the first year for companies with <$2M ARR.

**Q: What happens if I exceed my query limit?**
A: Queries continue to work, billed at $0.0005 per query above plan. You can set a hard cap in billing settings to prevent overage.

## Technical

**Q: What's the maximum query result size?**
A: 100K rows for inline display. Larger results are exported to Parquet/CSV and downloaded via signed URL.

**Q: Can I use the platform offline?**
A: No. Northwind is cloud-only. Edge / on-prem deployments are not supported.

**Q: How long does an initial sync take?**
A: Depends on data volume. A 100 GB warehouse typically syncs in 2-4 hours. Subsequent incremental syncs run in 1-15 minutes.

**Q: Do you have a SOC 2 report?**
A: Yes. SOC 2 Type II report available under NDA — request via security@northwind.cloud.
