# Security and Compliance

Northwind Cloud treats data security as a first-class concern. This document describes our security posture, certifications, and how customer data is protected.

## Certifications and compliance

- SOC 2 Type II audited annually by an independent firm
- ISO/IEC 27001:2022 certified
- HIPAA compliant infrastructure available on Enterprise plan
- GDPR and UK GDPR compliant; Data Processing Agreement available on request
- CCPA / CPRA compliant for California residents

## Data encryption

- **In transit**: TLS 1.3 enforced on all API and web traffic. Older TLS versions are rejected at the load balancer.
- **At rest**: AES-256 server-side encryption on all storage layers. Customer can supply own KMS key on Enterprise plan (BYOK).
- **Backups**: encrypted daily snapshots retained 30 days, replicated cross-region.

## Authentication

- Email + password with mandatory 2FA for Admin and Editor roles
- Single sign-on via SAML 2.0 (Okta, Azure AD, Google Workspace, OneLogin) on Business and Enterprise plans
- SCIM 2.0 user provisioning on Enterprise plan
- API keys with configurable scopes and expiry
- OAuth 2.0 device flow for CLI

## Network security

- VPC peering and PrivateLink available on Enterprise
- IP allowlisting per workspace on Business and above
- Web Application Firewall in front of all customer-facing endpoints
- DDoS mitigation via CloudFront

## Data residency

Customer data stays in the region selected at workspace creation. We do not move data across regions without explicit customer authorization. EU customers can pin to eu-west-1 or eu-central-1 for full GDPR compliance.

## Incident response

Security incidents are reported to affected customers within 24 hours of confirmation. Public security advisories are posted at status.northwind.cloud. Vulnerability reports can be submitted to security@northwind.cloud — we operate a public bug bounty via HackerOne.
