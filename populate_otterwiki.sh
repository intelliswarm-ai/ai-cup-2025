#!/bin/bash

# Script to populate OtterWiki with company policy pages

# Security Policy
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/security-policy.md << "EOF"
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
Report suspected phishing emails to security@intelliswarm.com immediately.

## 5. Data Classification
Mark emails containing sensitive data as CONFIDENTIAL.
EOF'

# Financial Procedures
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/financial-procedures.md << "EOF"
# Financial Transaction Procedures

All financial transactions must follow these procedures:

## 1. Wire Transfer Authorization
Wire transfers require dual approval from Finance Director and CFO. Requests via email must be verified by phone.

## 2. Invoice Verification
Verify all invoices match purchase orders before payment. Check vendor information in our approved vendor list.

## 3. Banking Information
Never update banking details based solely on email requests. Always verify through known contact channels.

## 4. Payment Fraud Prevention
Be alert for:
- Urgent payment requests
- Last-minute banking detail changes
- Pressure to bypass normal procedures
- Requests to keep transactions confidential

## 5. Expense Reporting
Submit expense reports through the official portal, not via email attachments.
EOF'

# IT Support Procedures
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/it-support-procedures.md << "EOF"
# IT Support Policy

Official IT support procedures:

## 1. Help Desk
Submit all IT requests through the help desk portal at helpdesk.intelliswarm.com

## 2. Account Issues
IT will NEVER ask for your password via email, phone, or chat. Use the password reset portal for account issues.

## 3. Software Updates
All software updates are pushed automatically. Ignore emails asking you to download software updates.

## 4. Legitimate IT Contacts
- Help Desk: support@intelliswarm.com
- IT Security: itsec@intelliswarm.com
- Phone: ext. 5555

## 5. Suspicious IT Requests
Report emails claiming to be from IT that:
- Request password or credentials
- Ask to download software from external sites
- Create urgency about account suspension
- Use non-company email addresses
EOF'

# Meeting Policy
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/meeting-policy.md << "EOF"
# Meeting and Calendar Policy

Company guidelines for meetings and calendar invites:

## 1. Meeting Invitations
All official meetings use company Outlook/Google Calendar. External calendar invites (.ics files) should be verified.

## 2. Video Conferencing
Use company-approved platforms:
- Microsoft Teams (primary)
- Zoom (with company SSO)
- Google Meet (with @intelliswarm.com accounts)

## 3. External Meetings
Verify external meeting requests by:
- Confirming with the organizer via known contact
- Checking if the meeting relates to your role
- Verifying the meeting platform is legitimate

## 4. Calendar Permissions
Never grant calendar editing permissions to external parties.

## 5. Meeting Recording
Inform participants before recording any meeting.
EOF'

# Data Protection
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/data-protection.md << "EOF"
# Data Protection and Privacy Policy

Guidelines for handling company and customer data:

## 1. Personal Information
Handle all personal data per GDPR and data protection regulations. Never share customer data via unsecured email.

## 2. Email Encryption
Use encrypted email for sensitive information. Enable encryption in Outlook/Gmail for:
- Customer PII
- Financial data
- Proprietary information

## 3. External Sharing
Before sharing data externally:
- Verify recipient authority
- Use secure file sharing (OneDrive, SharePoint)
- Apply appropriate access controls
- Set expiration dates

## 4. Data Breach Response
Report potential data breaches to dpo@intelliswarm.com within 24 hours.

## 5. Retention Policy
Follow data retention schedules. Don't keep sensitive emails beyond required period.
EOF'

# Vendor Management
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/vendor-management.md << "EOF"
# Vendor and Supplier Policy

Procedures for working with external vendors:

## 1. Approved Vendors
Use only approved vendors from the procurement portal. New vendor requests require Procurement approval.

## 2. Vendor Communications
Verify vendor emails match our records. Be suspicious of:
- New contacts from known vendors
- Urgent payment requests
- Banking detail changes
- Requests to bypass procurement

## 3. Contract Requirements
All vendor contracts must:
- Include security requirements
- Specify data handling procedures
- Define liability and insurance
- Be reviewed by Legal

## 4. Performance Reporting
Report vendor issues to procurement@intelliswarm.com

## 5. Vendor Access
External vendors require sponsor approval for system access.
EOF'

# HR Policies
docker exec mailbox-otterwiki bash -c 'cat > /app-data/repository/hr-policies.md << "EOF"
# Human Resources Policies

Important HR information for all employees:

## 1. Performance Reviews
Annual reviews conducted in Q1. HR will never request personal information via email.

## 2. Payroll
Payroll changes must be submitted through the HR portal. Direct deposit changes require identity verification.

## 3. Benefits
Open enrollment information sent via official HR communications. Verify links go to benefits.intelliswarm.com

## 4. Onboarding
New hire documentation completed through secure HR portal, not email attachments.

## 5. Legitimate HR Contacts
- General HR: hr@intelliswarm.com
- Payroll: payroll@intelliswarm.com
- Benefits: benefits@intelliswarm.com

## 6. Suspicious HR Emails
Report emails requesting:
- Social Security numbers
- Bank account details
- W-2 forms
- Personal information updates via email
EOF'

# Commit changes
docker exec mailbox-otterwiki bash -c 'cd /app-data/repository && git add *.md && git config user.name "System" && git config user.email "system@intelliswarm.com" && git commit -m "Add company policy pages"'

echo "✅ Successfully populated OtterWiki with 7 company policy pages!"
