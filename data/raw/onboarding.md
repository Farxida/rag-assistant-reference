# Onboarding for Teams

This guide is for teams setting up Northwind Cloud at the organization level. For individual setup, see Getting Started.

## Choosing the right plan

For most teams of 5-50 users, the **Business plan** is the right starting point. It includes SSO, audit logs, and the SLA you'll need for production use.

Consider Enterprise if you need:
- HIPAA compliance
- Single-tenant deployment
- 99.95% uptime SLA
- Dedicated support engineer
- Custom contract terms

## Identity setup (SSO)

We strongly recommend SSO for any team with 10+ users. Setup steps:

1. **In Northwind**: go to **Settings → SSO → Configure**
2. **In your IdP** (Okta, Azure AD, etc.): create a new SAML 2.0 application using the metadata URL from step 1
3. Map IdP groups to Northwind roles (Admin, Editor, Viewer)
4. Enable SCIM provisioning for automatic user lifecycle (Enterprise)

Once SSO is enabled, password authentication can be disabled to enforce IdP-only access.

## Permission model

### Roles (workspace-level)
- **Admin**: full access including billing, SSO, user management
- **Editor**: create and modify dashboards, run queries, manage data sources
- **Viewer**: read-only access to dashboards they have been granted

### Folders and granular permissions
- Dashboards live in folders
- Folder permissions: view-only, edit, manage (cascades to all dashboards inside)
- Specific dashboards can override folder permissions

### Recommended structure
- **/Public**: company-wide dashboards, all employees can view
- **/Engineering**: engineering team folder, restricted by IdP group
- **/Sales**: sales team folder, restricted to sales group + executives
- **/Drafts/[user]**: personal scratch folders

## Data governance

### Tagging
- Tag data sources with sensitivity levels: Public, Internal, Confidential, Restricted
- Tag flows to dashboards using those sources
- Set policies preventing low-clearance users from creating dashboards on Confidential data

### Audit logs
- Every query, dashboard view, and admin action is logged
- Logs visible in **Settings → Audit log** (Admin only)
- Logs exportable to S3 or sent to Datadog/Splunk in real time
- Retention: 12 months on Business, 7 years on Enterprise

## Cost controls

- Set workspace-level query budget cap
- Set per-user query rate limits
- Receive email when 75%, 90%, 100% of monthly budget reached
- Hard cap option: reject new queries above 100% of budget

## Training and adoption

For teams adopting Northwind:

1. **Week 1**: identify 2-3 power users to champion adoption
2. **Week 2**: import your top 5 most-used legacy dashboards
3. **Week 3**: shadow training session (we host free webinars Thursdays)
4. **Week 4**: deprecate old dashboards, redirect URLs to Northwind

Most teams reach productive usage in 2-4 weeks. Enterprise customers receive dedicated onboarding from their assigned engineer.
