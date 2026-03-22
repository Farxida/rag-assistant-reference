# Policies and Terms

This page summarizes Northwind Cloud's key policies. Full legal documents are at northwind.cloud/legal.

## Terms of Service

By using Northwind Cloud you agree to:
- Not reverse-engineer the platform or attempt to bypass rate limits
- Not store illegal content, malware, or violate third-party copyrights
- Not use the platform for cryptocurrency mining, password cracking, or DDoS
- Comply with applicable export control laws (US OFAC, EU sanctions)

We reserve the right to suspend accounts violating these terms with 24h written notice (immediate suspension for severe violations).

## Privacy Policy

### What we collect
- Account info: email, name, organization
- Usage data: queries run, dashboards viewed, features used (aggregated for product improvement)
- Customer data: only what you explicitly upload or connect (we are a Data Processor under GDPR)

### What we don't collect
- We don't track you across other websites
- We don't sell or share data with advertisers
- We don't use customer data to train AI models (see also AI Policy below)

### Cookies
- Essential cookies for authentication (required)
- Analytics cookies (Mixpanel, can be opted out)
- No third-party advertising cookies

## AI Usage Policy

- Customer data is **never** used to train shared AI models
- Embeddings are generated locally per workspace and stored encrypted
- LLM calls (e.g., natural-language to SQL) send only the user's query plus relevant schema, not data values
- Per-customer fine-tuning available on Enterprise with explicit opt-in and DPA amendment

## Service Level Agreement (SLA)

| Plan | Uptime SLA | Support response | Credit policy |
|------|-----------|-----------------|---------------|
| Free / Starter | None | 24-48h | None |
| Business | 99.9% | 4h business hours | 10% / 25% / 50% credit per tier of breach |
| Enterprise | 99.95% | 1h 24/7 | Custom per contract |

Uptime is measured against the public status page at status.northwind.cloud. Scheduled maintenance is excluded from SLA calculations and announced 7+ days in advance.

## Data Retention

- Active workspaces: data retained as long as subscription is active
- Cancelled workspaces: data retained 30 days, then permanently deleted
- Deleted accounts: backups retained 90 days for disaster recovery, then purged
- Audit logs: retained 12 months on Business, 7 years on Enterprise (regulatory requirement)

## Acceptable Use

What Northwind is not for:
- Storing personal medical records (use HIPAA-compliant Enterprise tier if you must)
- Real-time operational alerting (use PagerDuty / Datadog)
- Long-term archival storage (use S3 Glacier or equivalent)
- Mission-critical financial transactions (we are an analytics platform, not an OLTP database)

Violations may result in suspension. We will work with customers to migrate to appropriate solutions before terminating service.
