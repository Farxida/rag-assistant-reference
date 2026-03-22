# Regions and SLA

## Available regions

Northwind Cloud is available in five geographic regions:

| Region code | Location | Compliance | Data residency |
|---|---|---|---|
| us-east-1 | Virginia, USA | SOC 2, HIPAA | US |
| us-west-2 | Oregon, USA | SOC 2, HIPAA | US |
| eu-west-1 | Ireland | SOC 2, GDPR | EU |
| eu-central-1 | Frankfurt | SOC 2, GDPR | EU |
| ap-southeast-1 | Singapore | SOC 2 | APAC |

You select your region when creating a workspace. **Region cannot be changed after creation** — moving data requires creating a new workspace and re-syncing.

## SLA details

### Uptime targets
- **Business plan**: 99.9% monthly (43 minutes max downtime per month)
- **Enterprise plan**: 99.95% monthly (22 minutes max downtime per month)

### What's covered
- Web app availability (app.northwind.cloud)
- API availability (api.northwind.cloud)
- Query engine response time under documented limits
- Authentication services

### What's excluded from SLA
- Issues caused by customer configuration (e.g., wrong firewall rules)
- Force majeure events (natural disasters, war, government actions)
- Third-party service outages (e.g., AWS regional outage affecting us-east-1)
- Scheduled maintenance windows (announced 7+ days in advance)
- Beta features (clearly labeled in the UI)

### SLA credits

If we fall below the SLA in a month, you receive credits applied to next invoice:

| Uptime | Credit |
|--------|--------|
| 99.0% – 99.9% | 10% |
| 95.0% – 99.0% | 25% |
| Below 95.0% | 50% |

To claim credits, file a ticket within 30 days of the affected month. Credits are not paid in cash and do not exceed your monthly invoice.

### Support response times

| Severity | Business plan | Enterprise plan |
|----------|---------------|-----------------|
| P1 (production down) | 4h business hours | 1h 24/7 |
| P2 (major impact) | 4h business hours | 4h 24/7 |
| P3 (minor issue) | 8h business hours | 1 business day |
| P4 (question / FR) | 1 business day | 2 business days |

Business hours are 9am-6pm ET, Monday through Friday excluding US federal holidays. Enterprise customers receive 24/7 coverage with a dedicated support engineer assigned to their account.
