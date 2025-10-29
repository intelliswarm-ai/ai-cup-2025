#!/bin/bash
# Create wiki pages matching backend's fallback knowledge base

# Security Policy
docker exec mailbox-otterwiki bash -c 'mkdir -p /app-data/repository && cat > /app-data/repository/security-policy.md << "EOF"
# Security Policy

Our company has strict security protocols to protect against phishing and social engineering attacks:

## 1. Password Requirements
All passwords must be at least 12 characters with complexity requirements. Never share passwords via email.

## 2. Multi-Factor Authentication (MFA)
MFA is mandatory for all email accounts and internal systems.

## 3. Email Verification
Always verify sender authenticity before clicking links or downloading attachments. Check for:
- Suspicious sender addresses
- Urgent language requesting immediate action
- Requests for sensitive information
- Unusual attachments or links

## 4. Phishing Reporting
Report suspected phishing emails to the security team immediately.

## 5. Data Classification
Mark emails containing sensitive data as CONFIDENTIAL.
EOF'

# IT Support Procedures
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/it-support-procedures.md << "EOF"
# IT Support Procedures

Official IT support procedures:

## 1. Help Desk
Submit all IT requests through the help desk portal.

## 2. Account Issues
IT will NEVER ask for your password via email, phone, or chat. Use the password reset portal for account issues.

## 3. Software Updates
All software updates are pushed automatically. Ignore emails asking you to download software updates.

## 4. Legitimate IT Contacts
- Help Desk: Official support email only
- IT Security: Official security team contact
- Phone: Official company extensions only

## 5. Suspicious IT Requests
Report emails claiming to be from IT that request passwords or credentials.
EOF'

# HR Policies
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/hr-policies.md << "EOF"
# HR Policies

Important HR information for all employees:

## 1. Performance Reviews
Annual reviews conducted in Q1. HR will never request personal information via email.

## 2. Payroll
Payroll changes must be submitted through the HR portal. Direct deposit changes require identity verification.

## 3. Benefits
Open enrollment information sent via official HR communications. Verify links are from official company domains.

## 4. Onboarding
New hire documentation completed through secure HR portal, not email attachments.

## 5. Suspicious HR Emails
Report emails requesting Social Security numbers, bank account details, or W-2 forms via email.
EOF'

# Data Protection
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/data-protection.md << "EOF"
# Data Protection

Guidelines for handling company and customer data:

## 1. Personal Information
Handle all personal data per GDPR and data protection regulations. Never share customer data via unsecured email.

## 2. Email Encryption
Use encrypted email for sensitive information (customer PII, financial data, proprietary information).

## 3. External Sharing
Before sharing data externally, verify recipient authority and use secure file sharing.

## 4. Data Breach Response
Report potential data breaches to the data protection officer within 24 hours.

## 5. Retention Policy
Follow data retention schedules. Don't keep sensitive emails beyond required period.
EOF'

# Financial Procedures
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/financial-procedures.md << "EOF"
# Financial Procedures

All financial transactions must follow these procedures:

## 1. Wire Transfer Authorization
Wire transfers require dual approval from Finance Director and CFO. Requests via email must be verified by phone.

## 2. Invoice Verification
Verify all invoices match purchase orders before payment.

## 3. Banking Information
Never update banking details based solely on email requests. Always verify through known contact channels.

## 4. Payment Fraud Prevention
Be alert for urgent payment requests and last-minute banking detail changes.
EOF'

# Meeting Policy
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/meeting-policy.md << "EOF"
# Meeting Policy

Company guidelines for meetings and calendar invites:

## 1. Meeting Invitations
All official meetings use company Outlook/Google Calendar. External calendar invites should be verified.

## 2. Video Conferencing
Use company-approved platforms (Microsoft Teams, Zoom with SSO, Google Meet).

## 3. External Meetings
Verify external meeting requests by confirming with the organizer via known contact.
EOF'

# Vendor Management
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/vendor-management.md << "EOF"
# Vendor Management

Procedures for working with external vendors:

## 1. Approved Vendors
Use only approved vendors from the procurement portal.

## 2. Vendor Communications
Verify vendor emails match our records. Be suspicious of new contacts or urgent requests.

## 3. Contract Requirements
All vendor contracts must be reviewed by Legal.
EOF'

# Conference and Events
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/conference-and-events.md << "EOF"
# Conference and Events

Guidelines for attending and organizing company events:

## 1. Conference Registration
All conference attendance requires manager approval.

## 2. Event Types
Industry conferences, professional networking, training seminars, customer events.

## 3. Suspicious Event Emails
Be cautious of free registrations from unknown sources or requests for payment to personal accounts.
EOF'

# Performance Feedback
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/performance-feedback.md << "EOF"
# Performance Feedback

Performance review process and feedback guidelines:

## 1. Annual Performance Reviews
Conducted quarterly with formal annual review including self-assessment and manager evaluation.

## 2. Continuous Feedback
Managers provide ongoing feedback with monthly one-on-one meetings.

## 3. Review Documentation
All feedback documented in HR system. Never share performance information via unsecured email.
EOF'

# Project Documentation
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/project-documentation.md << "EOF"
# Project Documentation

Guidelines for creating and managing project documentation:

## 1. Documentation Requirements
All projects must maintain charter, requirements, specifications, and user guides.

## 2. Documentation Tools
Use Confluence, SharePoint, or GitHub for project documentation.

## 3. Version Control
Use semantic versioning and track all changes with revision history.
EOF'

# Status Reports and Updates
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/status-reports-and-updates.md << "EOF"
# Status Reports and Updates

Guidelines for weekly status reports and project updates:

## 1. Weekly Status Reports
Submit by Friday EOD including accomplishments, planned activities, blockers, and risks.

## 2. Report Format
Include executive summary, metrics, planned items, issues, and decisions needed.

## 3. Escalation
Flag critical issues immediately, don't wait for weekly report.
EOF'

# Budget and Planning
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/budget-and-planning.md << "EOF"
# Budget and Planning

Budget planning and financial management guidelines:

## 1. Annual Budget Cycle
Budget planning begins Q3 for following fiscal year.

## 2. Budget Approval Levels
Different approval levels based on amount (Manager, Director, VP, Executive).

## 3. Expense Tracking
Monitor spending against budget monthly with variance analysis.
EOF'

# Schedule and Calendar Management
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/schedule-and-calendar-management.md << "EOF"
# Schedule and Calendar Management

Best practices for managing schedules and calendar coordination:

## 1. Calendar Etiquette
Send meeting invites 24 hours in advance with agenda and objectives.

## 2. Meeting Scheduling
Check availability, use scheduling tools, avoid back-to-back meetings.

## 3. Schedule Confirmations
Confirm important meetings 24 hours in advance and verify details.
EOF'

# Commit all changes to git
docker exec mailbox-otterwiki bash -c 'cd /app-data/repository && git config user.name "System" && git config user.email "system@company.com" && git add . && git commit -m "Add company policy wiki pages" 2>/dev/null || echo "Pages already exist or commit failed"'

echo "✅ Successfully created wiki pages!"
echo "Pages created:"
echo "  - security-policy"
echo "  - it-support-procedures"
echo "  - hr-policies"
echo "  - data-protection"
echo "  - financial-procedures"
echo "  - meeting-policy"
echo "  - vendor-management"
echo "  - conference-and-events"
echo "  - performance-feedback"
echo "  - project-documentation"
echo "  - status-reports-and-updates"
echo "  - budget-and-planning"
echo "  - schedule-and-calendar-management"
