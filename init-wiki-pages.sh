#!/bin/bash

# Wiki Initialization Script
# Populates OtterWiki with comprehensive company knowledge base
# Runs automatically on container startup

WIKI_DIR="/app/wiki-pages"
WIKI_API="http://localhost:8080"

echo "=================================================="
echo "Initializing Company Wiki Knowledge Base"
echo "=================================================="
echo ""

# Wait for OtterWiki to be ready
echo "Waiting for OtterWiki to start..."
for i in {1..30}; do
  if curl -s "$WIKI_API" > /dev/null 2>&1; then
    echo "✓ OtterWiki is ready!"
    break
  fi
  echo "  Attempt $i/30..."
  sleep 2
done

# Create wiki pages directory
mkdir -p "$WIKI_DIR"

# Function to create wiki page
create_wiki_page() {
  local filename="$1"
  local title="$2"
  local content="$3"

  echo "Creating wiki page: $title"

  cat > "$WIKI_DIR/$filename" << 'WIKICONTENT'
$content
WIKICONTENT

  # Copy to OtterWiki data directory if it exists
  if [ -d "/app/data" ]; then
    cp "$WIKI_DIR/$filename" "/app/data/$filename"
  fi
}

# ============================================
# SECURITY AND COMPLIANCE
# ============================================

create_wiki_page "Security-Policy.md" "Security Policy" '# Security Policy

## Overview
Comprehensive security policies to protect company data and prevent cyber threats.

## Password Management

### Password Requirements
- Minimum 12 characters length
- Must include: uppercase, lowercase, numbers, special characters
- Cannot reuse last 5 passwords
- Must change every 90 days
- Never share passwords via email or messaging

### Password Best Practices
- Use unique passwords for each account
- Use password manager (LastPass, 1Password)
- Enable password complexity requirements
- Never write passwords down
- Report compromised passwords immediately

## Multi-Factor Authentication (MFA)

### MFA Requirements
- **Mandatory** for all employee accounts
- **Mandatory** for email access
- **Mandatory** for VPN connections
- **Mandatory** for admin/privileged accounts

### Supported MFA Methods
1. Microsoft Authenticator (preferred)
2. Google Authenticator
3. Hardware security keys (YubiKey)
4. SMS codes (fallback only)

## Email Security

### Email Verification Guidelines
Always verify email authenticity before:
- Clicking links
- Downloading attachments
- Providing information
- Taking requested actions

### Red Flags for Phishing
- **Suspicious sender addresses** (typos, unusual domains)
- **Urgent language** ("act now", "expires today")
- **Requests for credentials** or sensitive data
- **Generic greetings** ("Dear customer")
- **Unusual attachments** (.exe, .zip from unknown senders)
- **Mismatched URLs** (hover to check real destination)

### Reporting Phishing
1. Do NOT click links or reply
2. Forward to security@company.com
3. Use "Report Phishing" button in email client
4. Delete after reporting

## Data Classification

### Classification Levels
- **Public**: Can be freely shared (marketing materials)
- **Internal**: Company use only (policies, procedures)
- **Confidential**: Restricted access (employee data, contracts)
- **Highly Confidential**: Severely restricted (financials, trade secrets)

### Email Markings
Mark emails with sensitive data:
- Subject line: [CONFIDENTIAL] or [INTERNAL]
- Use encryption for confidential data
- Verify recipients before sending

## Access Control

### Account Access
- Use least privilege principle
- Request access through IT portal
- Manager approval required
- Regular access reviews quarterly

### Remote Access
- VPN required for remote work
- Multi-factor authentication mandatory
- Company-managed devices only
- No public WiFi for sensitive work

## Security Incident Reporting

### What to Report
- Suspected phishing emails
- Lost or stolen devices
- Unauthorized access attempts
- Data breaches or leaks
- Malware infections
- Security policy violations

### How to Report
- **Immediate**: Email security@company.com
- **Urgent**: Call Security Hotline (24/7)
- **Portal**: Submit ticket in IT Security Portal

### Response Time
- Critical incidents: <15 minutes
- High priority: <1 hour
- Medium priority: <4 hours
- Low priority: <24 hours
'

create_wiki_page "Data-Protection-and-Privacy.md" "Data Protection and Privacy" '# Data Protection and Privacy

## GDPR and Privacy Compliance

### Personal Data Definition
Personal data includes any information relating to an identified or identifiable person:
- Names, email addresses, phone numbers
- Employee IDs, social security numbers
- IP addresses, location data
- Financial information
- Health records
- Biometric data

### Data Protection Principles
1. **Lawfulness, fairness, transparency**
2. **Purpose limitation** - collect only for specified purposes
3. **Data minimization** - only collect what is necessary
4. **Accuracy** - keep data accurate and up-to-date
5. **Storage limitation** - keep only as long as needed
6. **Integrity and confidentiality** - protect against unauthorized access
7. **Accountability** - demonstrate compliance

## Email Data Protection

### Sending Personal Data
- Use encryption for customer PII
- Use encrypted email for:
  - Customer personal information
  - Financial data
  - Health records
  - Proprietary information
  - Legal documents

### Email Encryption
- Enable S/MIME in Outlook
- Use "Encrypt" button in Gmail
- For external recipients: Use secure file sharing instead

### Data Sharing Rules
Before sharing customer data:
1. Verify recipient has business need
2. Confirm recipient is authorized
3. Use minimum necessary data
4. Apply appropriate security controls
5. Log the data transfer

## External Data Sharing

### Secure File Sharing
Approved platforms:
- **OneDrive for Business** (internal/external)
- **SharePoint** (internal)
- **Secure File Transfer** (large files to external parties)

Never use:
- Personal cloud storage (Dropbox, Google Drive personal)
- Unencrypted email attachments
- USB drives for confidential data
- Public file sharing sites

### Access Controls
When sharing externally:
- Set expiration dates (30 days max)
- Require authentication
- Limit to view-only when possible
- Track access and downloads
- Revoke access when no longer needed

## Data Breach Response

### What is a Data Breach?
- Unauthorized access to personal data
- Accidental disclosure of sensitive information
- Lost or stolen devices with data
- Email sent to wrong recipient
- Ransomware or malware infection

### Reporting Requirements
- **Immediately**: Notify Data Protection Officer (DPO)
- **Within 24 hours**: Incident report submitted
- **Within 72 hours**: Regulatory notification if required

### Contact Information
- Data Protection Officer: dpo@company.com
- Security Team: security@company.com
- IT Support: helpdesk@company.com

## Data Retention

### Email Retention Policy
- **Business emails**: Retain 7 years
- **HR records**: Retain per legal requirements
- **Financial records**: Retain 10 years
- **Temporary communications**: Delete after 90 days
- **Personal emails**: Not retained

### Data Disposal
- Delete data when no longer needed
- Shred physical documents
- Wipe devices before disposal
- Certify data destruction
- Maintain disposal logs

## Employee Rights

### Data Subject Rights
Employees have the right to:
- Access their personal data
- Correct inaccurate data
- Request data deletion
- Object to processing
- Data portability

### How to Exercise Rights
Submit requests to: privacy@company.com
Response time: Within 30 days
'

# ============================================
# HR AND PEOPLE MANAGEMENT
# ============================================

create_wiki_page "Performance-Reviews-and-Feedback.md" "Performance Reviews and Feedback" '# Performance Reviews and Feedback

## Performance Review Process

### Annual Review Cycle

**Timeline:**
- **Q1 (Jan-Mar)**: Goal setting and planning
- **Q2 (Apr-Jun)**: Mid-year checkpoint
- **Q3 (Jul-Sep)**: Progress review
- **Q4 (Oct-Dec)**: Annual performance review

### Review Steps
1. **Self-Assessment** (2 weeks before review)
   - Reflect on accomplishments
   - Assess goal achievement
   - Identify development areas
   - Prepare examples and metrics

2. **Manager Evaluation** (1 week before meeting)
   - Review employee self-assessment
   - Gather peer feedback
   - Assess performance against goals
   - Prepare rating and recommendations

3. **Review Meeting** (60-90 minutes)
   - Discuss achievements and challenges
   - Review goals and ratings
   - Identify development opportunities
   - Set goals for next period

4. **Documentation** (Within 3 days)
   - Submit review in HR system
   - Employee acknowledges review
   - Development plan finalized

## Performance Ratings

### Rating Scale
- **Exceeds Expectations (5)**: Consistently exceeds all goals
- **Exceeds in Some Areas (4)**: Exceeds some goals, meets others
- **Meets Expectations (3)**: Consistently meets all goals
- **Needs Improvement (2)**: Meets some goals, misses others
- **Unsatisfactory (1)**: Consistently fails to meet goals

### Rating Distribution
Target distribution:
- 10% - Exceeds (5)
- 25% - Exceeds Some (4)
- 50% - Meets (3)
- 10% - Needs Improvement (2)
- 5% - Unsatisfactory (1)

## Continuous Feedback

### Regular One-on-Ones
- **Frequency**: Bi-weekly (minimum monthly)
- **Duration**: 30-60 minutes
- **Agenda**:
  - Progress on current goals
  - Challenges and blockers
  - Career development
  - Feedback (both directions)
  - Personal check-in

### Feedback Best Practices

**Giving Feedback:**
- **Timely**: Provide soon after observation
- **Specific**: Use concrete examples
- **Behavioral**: Focus on actions, not personality
- **Balanced**: Include strengths and development areas
- **Actionable**: Suggest specific improvements

**Receiving Feedback:**
- **Listen actively**: Don't interrupt or defend
- **Clarify**: Ask questions to understand
- **Reflect**: Consider the feedback objectively
- **Act**: Develop action plan for improvement
- **Follow up**: Share progress with feedback provider

## 360-Degree Feedback

### Process
**Who Provides Feedback:**
- Direct manager
- Peers (3-5 colleagues)
- Direct reports (if applicable)
- Cross-functional partners
- Self-assessment

**Timeline:**
- Nomination: 2 weeks before review
- Feedback collection: 1 week
- Aggregation: 3 days
- Review meeting: 1 week after aggregation

**Questions Cover:**
- Collaboration and teamwork
- Communication skills
- Technical competence
- Leadership and initiative
- Cultural fit and values

### Confidentiality
- Feedback is aggregated and anonymized
- Minimum 3 respondents for peer feedback
- Used for development, not compensation
- Shared only with employee and manager

## Performance Improvement Plans (PIP)

### When PIPs Are Used
- Consistent underperformance
- Behavioral issues
- Skills gaps
- After informal coaching hasn't worked

### PIP Components
1. **Performance Issues**: Specific areas needing improvement
2. **Success Criteria**: Clear, measurable goals
3. **Support Plan**: Resources, training, mentoring
4. **Timeline**: Usually 30-90 days
5. **Check-ins**: Weekly progress meetings
6. **Outcomes**: Extension, successful completion, or termination

### PIP Process
1. HR consultation
2. PIP document creation
3. Initial PIP meeting
4. Weekly check-ins
5. Mid-point review
6. Final assessment
7. Outcome determination

## Goal Setting

### SMART Goals
- **Specific**: Clear and well-defined
- **Measurable**: Quantifiable success criteria
- **Achievable**: Realistic given resources
- **Relevant**: Aligned with team/company objectives
- **Time-bound**: Clear deadline

### Goal Categories
- **Business Results** (40%): Revenue, projects, deliverables
- **Operational Excellence** (30%): Quality, efficiency, process
- **People Development** (20%): Skills, mentoring, collaboration
- **Innovation** (10%): New ideas, improvements, learning

### Goal Examples

**Good Goals:**
- "Increase customer satisfaction score from 7.5 to 8.2 by Q4"
- "Launch 3 new product features by June 30 meeting quality standards"
- "Reduce deployment time by 50% through automation by end of Q2"

**Poor Goals:**
- "Do better at customer service" (not specific or measurable)
- "Work on some projects" (not specific or time-bound)
- "Be a team player" (not measurable)

## Career Development

### Development Planning
1. **Assess current skills**: Self-assessment + manager input
2. **Identify gaps**: Compare to target role requirements
3. **Create plan**: Training, mentoring, stretch assignments
4. **Execute**: Complete development activities
5. **Measure progress**: Regular check-ins and milestones

### Development Resources
- **Training**: LinkedIn Learning, Coursera, internal courses
- **Mentoring**: Internal mentorship program
- **Conferences**: Industry events (with manager approval)
- **Stretch Assignments**: New responsibilities, projects
- **Job Shadowing**: Learn from other teams
- **Certifications**: Professional certifications (company-sponsored)

## Documentation and Privacy

### What is Documented
- Performance ratings and reviews
- Goal achievement
- Development plans
- Feedback summaries
- PIP documents

### Access and Confidentiality
- Stored in secure HR system
- Access limited to: employee, manager, HR, senior leadership
- Never share performance information via email
- Comply with data protection regulations
- Retained per legal requirements
'

create_wiki_page "Employee-Onboarding-and-Welcome.md" "Employee Onboarding and Welcome" '# Employee Onboarding and Welcome

## New Hire Onboarding Process

### Pre-Arrival (2 Weeks Before Start)

**HR Tasks:**
- Send welcome email with start date, time, location
- Provide pre-boarding checklist
- Share company handbook and policies
- Request completion of employment forms
- Coordinate background check and drug screening
- Order employee badge and access cards

**IT Tasks:**
- Create user accounts (email, VPN, systems)
- Assign laptop and equipment
- Set up phone extension
- Configure access permissions
- Prepare workspace

**Manager Tasks:**
- Notify team of new hire
- Assign onboarding buddy
- Prepare 30-60-90 day plan
- Schedule first week meetings
- Organize team welcome lunch

### Day 1: Welcome and Orientation

**Morning (9 AM - 12 PM):**
- Welcome by manager
- HR orientation:
  - Benefits enrollment
  - Payroll setup
  - Company policies
  - Safety and security
- Office tour
- Badge and equipment pickup
- IT setup and training

**Afternoon (1 PM - 5 PM):**
- Team introductions
- Workspace setup
- Review role and expectations
- Overview of first week schedule
- Security and compliance training
- Welcome lunch with team

### Week 1: Foundation

**Key Activities:**
- Complete all IT setup
- Mandatory compliance training:
  - Security awareness
  - Data protection
  - Code of conduct
  - Harassment prevention
  - Safety procedures
- Meet with key stakeholders
- Review organizational structure
- Shadow team members
- Begin initial assignments

**Onboarding Checklist:**
- ☐ Email and calendar access verified
- ☐ VPN and remote access configured
- ☐ All systems access granted
- ☐ Emergency contact information submitted
- ☐ Benefits enrollment completed
- ☐ Direct deposit set up
- ☐ Compliance training completed
- ☐ Team introductions done
- ☐ 30-60-90 day plan reviewed

### Month 1: Integration (Days 1-30)

**Goals:**
- Understand company culture and values
- Learn team processes and workflows
- Complete onboarding training modules
- Establish relationships with team
- Deliver first small project or task

**Activities:**
- Weekly check-ins with manager
- Daily check-ins with onboarding buddy
- Attend team meetings
- Review documentation and resources
- Begin contributing to team projects
- Join company social events

**Week 1-2 Focus:** Learning and observation
**Week 3-4 Focus:** Active participation and contribution

### Month 2: Contribution (Days 31-60)

**Goals:**
- Take ownership of specific responsibilities
- Work independently on assigned tasks
- Understand broader team objectives
- Identify process improvements
- Build cross-functional relationships

**Activities:**
- Bi-weekly check-ins with manager
- Lead small projects or tasks
- Participate in team planning
- Attend department meetings
- Complete role-specific training

**Mid-Point Review (Day 45):**
- Review progress against 30-60-90 plan
- Discuss challenges and questions
- Adjust goals if needed
- Gather feedback from team
- Identify additional support needs

### Month 3: Full Productivity (Days 61-90)

**Goals:**
- Operate at full productivity level
- Own complete projects or work streams
- Mentor newer team members
- Contribute to team planning
- Propose improvements and innovations

**Activities:**
- Monthly check-ins with manager
- Full participation in team processes
- Take on stretch assignments
- Join cross-functional initiatives
- Begin setting individual goals

**90-Day Review:**
- Comprehensive performance assessment
- Review goal achievement
- Gather 360-degree feedback
- Discuss career development
- Set goals for next quarter
- Confirm continuation of employment

## Onboarding Documentation

### Required Documents (Complete Before Day 1)
- Employment application
- Background check authorization
- I-9 employment eligibility
- Tax withholding forms (W-4)
- Direct deposit information
- Emergency contact information
- Confidentiality agreement
- Acceptable use policy

### Training Modules (Complete Week 1)
- Company overview and history
- Mission, vision, values
- Organizational structure
- Products and services
- Security awareness
- Data protection and privacy
- Code of conduct
- Anti-harassment policy
- Safety and emergency procedures

## Onboarding Support

### Onboarding Buddy Program
**Buddy Responsibilities:**
- Answer questions about company culture
- Explain unwritten rules and norms
- Introduce to broader network
- Lunch together first week
- Daily check-ins first week
- Weekly check-ins first month
- Available for questions anytime

**Buddy Selection:**
- Same team or related function
- Different reporting line (not manager)
- 1+ years with company
- Strong cultural fit
- Volunteers for program

### Manager Support
**Manager Responsibilities:**
- Clear communication of expectations
- Regular check-ins and feedback
- Remove blockers and obstacles
- Provide necessary resources
- Introduce to key stakeholders
- Celebrate early wins
- Address concerns promptly

### HR Support
**Available Resources:**
- Onboarding portal and checklist
- Benefits information and enrollment
- Policy questions
- Payroll and compensation
- Career development resources
- Employee assistance program (EAP)

**Contact Information:**
- HR Generalist: hr@company.com
- Benefits: benefits@company.com
- Payroll: payroll@company.com
- IT Support: helpdesk@company.com

## Remote Onboarding

### Additional Considerations for Remote Employees

**Equipment Shipping:**
- Laptop shipped 1 week before start
- Monitors and accessories shipped separately
- Return shipping labels included
- Insurance and tracking provided

**Virtual Setup:**
- IT setup call on Day 1
- Video introductions with team
- Virtual office tour
- Digital onboarding checklist
- Virtual welcome event

**Communication:**
- Daily video check-ins first week
- Slack/Teams instant messaging
- Virtual coffee chats with team
- Video calls for all meetings
- Extra touchpoints for connection

**Engagement:**
- Virtual team building activities
- Digital swag package
- Online training modules
- Virtual happy hours
- Ship team care package

### Success Factors for Remote Onboarding
- Over-communicate expectations
- Provide extra documentation
- Schedule more frequent check-ins
- Create opportunities for informal connection
- Be patient with technical issues
- Encourage camera-on meetings
- Plan in-person visit when possible
'

# ============================================
# MEETINGS AND EVENTS
# ============================================

create_wiki_page "Conference-and-Event-Management.md" "Conference and Event Management" '# Conference and Event Management

## Conference Registration Process

### Approval Requirements

**Before Registering:**
1. Manager approval required for all conferences
2. Budget approval from finance
3. Travel approval if out of town
4. Calendar clearance (no conflicting priorities)

**Approval Levels:**
- Local events (<$500): Manager approval
- Regional conferences ($500-$2000): Director approval
- National conferences ($2000-$5000): VP approval
- International conferences (>$5000): Executive approval

### Registration Submission

**Required Information:**
- Conference name and organizer
- Dates and location
- Registration fee breakdown
- Travel costs estimate (flight, hotel, meals)
- Business justification
- Expected ROI and learning outcomes
- Presentation or speaking role (if applicable)

**Submission Process:**
1. Submit request via Events Portal
2. Attach conference agenda/brochure
3. Provide business case
4. Await approval (3-5 business days)
5. Register upon approval
6. Book travel through approved vendors

### Payment and Reimbursement

**Registration Fees:**
- Use corporate card when available
- Submit expense report within 30 days
- Attach conference confirmation
- Indicate budget code

**Travel Expenses:**
- Follow company travel policy
- Book through approved travel agency
- Itemized receipts required
- Per diem rates apply for meals

## Types of Events

### Industry Conferences
Large-scale events focusing on specific industries or technologies:
- Trade shows and exhibitions
- Technology summits
- Industry associations conferences
- Product launches and keynotes

**Benefits:**
- Industry trends and insights
- Product demos and vendors
- Networking with peers
- Professional development
- Brand visibility

### Networking Events
Focused on building professional relationships:
- Chamber of Commerce meetings
- Professional association meetups
- Industry mixers and socials
- Executive roundtables
- Customer appreciation events

**Best Practices:**
- Bring business cards
- Prepare elevator pitch
- Set connection goals (10-15 new contacts)
- Follow up within 48 hours
- Connect on LinkedIn

### Training Seminars
Educational events for skill development:
- Technical workshops
- Leadership development
- Certification programs
- Product training
- Compliance training

**Documentation:**
- Certificate of completion
- Training materials and notes
- Skills assessment
- Share learnings with team
- Update training records

### Company-Sponsored Events
Internal events organized by company:
- Annual kickoff meetings
- Team building events
- Town halls and all-hands
- Holiday parties
- Customer conferences

**Attendance:**
- Usually mandatory for relevant employees
- RSVP by deadline
- Coordinate coverage during event
- Participate actively
- Provide feedback

## Conference Attendance Guidelines

### Before the Conference

**Preparation (2-4 Weeks Before):**
- Review conference agenda and sessions
- Identify must-attend sessions
- Research speakers and attendees
- Schedule meetings with vendors/partners
- Prepare questions and discussion topics
- Update LinkedIn profile
- Order business cards

**Travel Arrangements:**
- Book flights and hotel 3+ weeks in advance
- Arrange ground transportation
- Set up out-of-office messages
- Delegate urgent responsibilities
- Pack professional attire and materials

### During the Conference

**Maximizing Value:**
- Attend keynote sessions
- Choose breakout sessions strategically
- Take detailed notes
- Participate in Q&A
- Visit expo hall/vendor booths
- Attend networking events
- Collect materials and swag

**Networking:**
- Introduce yourself to speakers
- Exchange contact information
- Join group discussions
- Attend social events
- Take photos (with permission)
- Live-tweet insights (if appropriate)

**Safety and Conduct:**
- Wear conference badge at all times
- Follow venue rules and policies
- Represent company professionally
- Respect code of conduct
- Report any incidents immediately

### After the Conference

**Follow-Up (Within 1 Week):**
- Send thank you emails to connections
- Connect on LinkedIn with new contacts
- Share key insights with team
- Write conference summary/report
- Submit expense report
- Update CRM with new leads

**Knowledge Sharing:**
- Present key learnings to team (30-60 min)
- Share presentations and materials
- Write blog post or article
- Update training materials
- Implement new ideas and processes

## Event Communications

### Official Event Communications

**Legitimate Sources:**
- Conference organizers with verified domains
- Professional associations (known contacts)
- Company events team (events@company.com)
- Approved vendors and partners

**Expected Content:**
- Event registration confirmations
- Schedule and agenda updates
- Venue and logistics information
- Speaker announcements
- Networking opportunities
- Post-event surveys

### Suspicious Event Emails

**Red Flags:**
- Free conferences from unknown sources
- Requests for payment to personal accounts
- Suspicious sender domains (typos, odd TLDs)
- Generic greetings ("Dear attendee")
- Urgent registration deadlines
- Requests for excessive personal information
- Last-minute venue changes without explanation
- Unverified conference platforms or apps

**Verification Steps:**
1. Check sender domain matches official site
2. Search conference name online
3. Verify on professional association sites
4. Contact organizer via known channels
5. Check if colleagues received same email
6. Report suspicious emails to security team

## Virtual Events and Webinars

### Webinar Platforms

**Approved Platforms:**
- Microsoft Teams (internal and external)
- Zoom (with corporate SSO)
- WebEx (corporate account)
- GoToWebinar (approved vendors only)

**Platform Security:**
- Require registration
- Enable waiting room
- Require authentication
- Disable screen sharing for attendees
- Record sessions for audit

### Virtual Event Best Practices

**Technical Preparation:**
- Test audio and video 15 minutes before
- Close unnecessary applications
- Use wired internet if possible
- Prepare backup connectivity (hotspot)
- Have phone dial-in ready
- Test screen sharing

**Professional Conduct:**
- Professional background or blur
- Appropriate lighting and camera angle
- Mute when not speaking
- Use video when possible
- Dress professionally (camera-on)
- Minimize distractions

**Engagement:**
- Use chat for questions
- Participate in polls and Q&A
- React with emojis/reactions
- Share insights in chat
- Network in breakout rooms

## Event ROI and Reporting

### Measuring Event Success

**Quantitative Metrics:**
- Number of connections made
- Leads generated
- Sales opportunities created
- Partnerships discussed
- Training certifications earned
- Cost per connection

**Qualitative Metrics:**
- Industry insights gained
- Competitive intelligence
- Brand visibility
- Thought leadership opportunities
- Team morale and engagement
- Skills and knowledge acquired

### Event Report Template

**Executive Summary:**
- Event name and dates
- Total cost and budget
- Key outcomes and ROI
- Recommendations

**Detailed Report:**
- Sessions attended and key learnings
- Connections made (with follow-up plan)
- Competitive insights
- Industry trends observed
- Action items for team
- Materials and resources gathered
- Photos and social media coverage

**Recommendations:**
- Should we attend next year?
- Changes for future attendance
- Sessions/tracks to prioritize
- Additional team members to send
- Sponsorship opportunities
'

create_wiki_page "Meeting-Coordination-and-Scheduling.md" "Meeting Coordination and Scheduling" '# Meeting Coordination and Scheduling

## Meeting Policy and Etiquette

### Scheduling Guidelines

**Advance Notice:**
- Regular meetings: 24 hours minimum
- Important meetings: 3-5 business days
- All-hands/town halls: 2 weeks
- External client meetings: 1 week
- Recurring meetings: Set up at start of quarter

**Timing Considerations:**
- Respect working hours (9 AM - 5 PM local time)
- Avoid lunch hours (12 PM - 1 PM)
- No meetings before 9 AM or after 5 PM without consent
- Allow 5-10 minute buffer between meetings
- Respect focus time blocks

**Meeting Length:**
- Status updates: 15-30 minutes
- Team meetings: 30-60 minutes
- Working sessions: 60-90 minutes
- Workshops: 2-4 hours
- All-hands: 60 minutes

### Calendar Etiquette

**Sending Invites:**
- Check availability before sending
- Include clear subject line
- Add detailed agenda
- Specify location or video link
- List required vs optional attendees
- Attach relevant materials
- Set appropriate reminders

**Responding to Invites:**
- Accept/decline within 24 hours
- Provide reason if declining
- Suggest alternative if needed
- Mark tentative if unsure
- Remove yourself if no longer needed
- Notify organizer of late arrival

**Calendar Management:**
- Keep calendar up-to-date
- Block focus time for deep work
- Mark out-of-office time
- Set working hours
- Update location (office/remote/travel)
- Make some time slots available

## Meeting Types

### Team Meetings

**Weekly Team Sync (30-60 minutes):**
- Round-robin updates from each member
- Project status and blockers
- Resource needs and dependencies
- Upcoming deadlines and priorities
- Team announcements
- Q&A and open discussion

**Agenda Template:**
1. Check-in (5 min)
2. Project updates (20 min)
3. Blockers and risks (10 min)
4. Upcoming work and priorities (10 min)
5. Announcements and Q&A (10 min)
6. Action items recap (5 min)

### One-on-One Meetings

**Manager/Employee 1:1s (30-60 minutes):**
- **Frequency**: Bi-weekly (minimum monthly)
- **Duration**: 30-60 minutes
- **Employee-led agenda**

**Discussion Topics:**
- Current project progress
- Challenges and support needed
- Career development and goals
- Feedback (both directions)
- Workload and priorities
- Personal well-being check-in

**Best Practices:**
- Prepare agenda in advance
- Take notes during meeting
- Follow up on action items
- Keep conversation confidential
- Focus on growth and development
- Don't cancel unless emergency

### All-Hands and Town Halls

**Company All-Hands (Quarterly):**
- Company performance updates
- Strategic initiatives and priorities
- Department highlights
- Leadership Q&A
- Recognition and celebrations
- Looking ahead

**Format:**
- Executive presentations (30 min)
- Department spotlights (15 min)
- Q&A session (15 min)
- Recording available for remote/absent employees

**Participation:**
- Submit questions in advance
- Use chat for live questions
- React and engage
- Take notes on key points

### Client and External Meetings

**Client Meetings:**
- Confirm 24 hours in advance
- Send agenda before meeting
- Test technology beforehand
- Join 2-3 minutes early
- Have backup plan ready
- Follow up with summary and action items

**Meeting Minutes:**
- Assign note-taker before meeting
- Document key decisions
- Track action items with owners
- Note open questions/issues
- Share within 24 hours
- Store in shared location

## Schedule Confirmations

### Confirmation Best Practices

**When to Confirm:**
- Important client meetings: 24 hours before
- Executive meetings: 24 hours before
- External partner meetings: 24 hours before
- Large group events: 2-3 days before
- First-time meetings: Day before

**Confirmation Template:**
```
Hi [Name],

This is a friendly reminder about our meeting tomorrow:

📅 Date: [Day, Month Date]
🕐 Time: [Time] - [Time] ([Timezone])
📍 Location: [Room/Video Link]
📋 Agenda: [Brief agenda or link]

Please let me know if you need to reschedule or if you have any questions.

Looking forward to speaking with you!

[Your Name]
```

**What to Include:**
- Date and time with timezone
- Location or video conferencing link
- Meeting purpose/agenda
- Any pre-work or materials to review
- Dial-in information (if applicable)
- Contact info for questions

### Rescheduling Meetings

**How to Reschedule:**
1. Notify ASAP (ideally 24+ hours notice)
2. Apologize for inconvenience
3. Provide reason (if appropriate)
4. Offer 2-3 alternative times
5. Send updated calendar invite

**Reschedule Template:**
```
Hi [Name],

I apologize, but I need to reschedule our meeting on [date/time] due to [brief reason].

Could we meet instead on one of these times?
- [Option 1]
- [Option 2]
- [Option 3]

Please let me know what works best for you, or feel free to suggest another time.

Thank you for your understanding.

[Your Name]
```

## Video Conferencing

### Approved Platforms

**Primary Platform:**
- **Microsoft Teams**: Default for all internal meetings

**Approved for External:**
- **Zoom**: Use company SSO account
- **Google Meet**: Use company Google account
- **WebEx**: For specific client requirements

**Never Use:**
- Personal accounts (personal Zoom, etc.)
- Unverified platforms
- Free public meeting rooms
- Platforms from unknown links

### Video Call Best Practices

**Technical Setup:**
- Test audio/video 5 minutes early
- Use headphones/earbuds for better audio
- Wired internet preferred over WiFi
- Close unnecessary applications
- Have phone dial-in as backup

**Professional Presence:**
- Camera on for important meetings
- Professional background or blur
- Appropriate lighting (face visible)
- Eye level camera position
- Dress professionally (at least top half)
- Minimize background noise

**During the Call:**
- Join 2-3 minutes early
- Mute when not speaking
- Unmute before speaking (avoid "You're on mute")
- Use "raise hand" feature for questions
- Use chat for links and notes
- Don't multitask visibly
- Stay engaged and attentive

### Screen Sharing

**Before Sharing:**
- Close confidential documents
- Disable notifications
- Close personal tabs/applications
- Clear desktop of sensitive files
- Check what's in view
- Use "share specific app" not "entire screen"

**While Sharing:**
- Narrate what you're showing
- Zoom in for readability
- Slow down mouse movements
- Pause for questions
- Don't switch between too many windows

## Time Zone Management

### Global Meeting Scheduling

**Time Zone Considerations:**
- Always specify timezone in invites
- Use "Find Time" tool for multi-timezone meetings
- Rotate meeting times if recurring globally
- Schedule during overlapping business hours when possible
- Record meetings for those who can't attend live

**Time Zone Tools:**
- World Clock in Outlook/Google Calendar
- Every Time Zone website
- Calendly with timezone detection
- When2Meet for group scheduling

**Best Practices:**
- Respect all participants' working hours
- Don't schedule early morning or late evening
- Allow asynchronous participation when possible
- Share recordings and notes
- Rotate "inconvenient" times fairly

### Meeting Time Examples

**9 AM Eastern = ?**
- 6 AM Pacific
- 2 PM London (GMT)
- 9 PM Singapore
- 11 PM Sydney

**Ideal Global Meeting Times:**
- 9-10 AM Eastern (afternoon Europe, late Asia)
- 1-2 PM Eastern (late afternoon Europe, early Asia)
- 8 AM Eastern (early Europe, late evening Asia)

## Recurring Meetings

### Managing Recurring Meetings

**When to Use:**
- Weekly team syncs
- Bi-weekly 1:1s
- Monthly all-hands
- Quarterly reviews
- Regular standups

**Setup Best Practices:**
- Set end date or review date
- Make series editable by organizer only
- Add agenda template in description
- Set up automated reminders
- Include video link for consistency

**Maintenance:**
- Review quarterly: Still needed?
- Update attendees as team changes
- Adjust frequency if needed
- Cancel individual instances when not needed
- Archive or delete if no longer needed

### Standing Meeting Review

**Questions to Ask:**
- Is this meeting still necessary?
- Can it be shorter?
- Are the right people attending?
- Can frequency be reduced?
- Can it be async (email update)?
- Is there a clear owner and agenda?

**When to Cancel:**
- Original purpose is complete
- Attendance consistently low
- Better handled asynchronously
- Duplicate of another meeting
- No longer adds value

## Meeting Rooms and Spaces

### Booking Conference Rooms

**Room Features:**
- Small rooms (2-4 people): Quick meetings, 1:1s
- Medium rooms (5-8 people): Team meetings
- Large rooms (9-15 people): Department meetings
- Boardrooms (10-20 people): Executive meetings, clients

**Equipment:**
- Video conferencing camera/mic
- Large display or projector
- Whiteboard
- Conference phone
- HDMI/USB-C connections

**Booking Process:**
1. Check room availability in calendar
2. Book room when scheduling meeting
3. Arrive on time or release early
4. End on time or extend if available
5. Leave room clean and reset

### Room Etiquette

**Before Meeting:**
- Check in advance room has needed equipment
- Arrive 5 minutes early to set up
- Ensure video conferencing works
- Adjust room layout if needed

**During Meeting:**
- Speak at appropriate volume
- Clean up food/drinks
- Use whiteboard markers (not permanent)
- Keep noise levels reasonable

**After Meeting:**
- Erase whiteboards
- Remove all materials
- Return furniture to default layout
- Dispose of trash
- End video call
- Release room if done early
'

echo "✓ All wiki pages created successfully!"
echo ""
echo "Wiki pages available:"
ls -1 "$WIKI_DIR/"
echo ""
echo "=================================================="
echo "Wiki initialization complete!"
echo "=================================================="
