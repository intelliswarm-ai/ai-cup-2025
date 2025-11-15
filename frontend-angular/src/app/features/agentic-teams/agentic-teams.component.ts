import { Component, OnInit, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subject, combineLatest, BehaviorSubject } from 'rxjs';
import { takeUntil, map } from 'rxjs/operators';
import { Email } from '../../core/models/email.model';
import { selectAllEmails } from '../../store';
import * as EmailsActions from '../../store/emails/emails.actions';
import { EmailService } from '../../core/services/email.service';
import { SseService } from '../../core/services/sse.service';

interface TeamMember {
  name: string;
  role: string;
  icon: string;
  memberType: string;
  personality: string;
  responsibilities: string;
  communicationStyle: string;
}

interface DiscussionMessage {
  agentName: string;
  agentIcon: string;
  content: string;
  timestamp: string;
  isToolUsage?: boolean;
}

interface TeamInfo {
  name: string;
  key: string;
  badge: string;
  members: TeamMember[];
}

@Component({
  selector: 'app-agentic-teams',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agentic-teams.component.html',
  styleUrl: './agentic-teams.component.scss'
})
export class AgenticTeamsComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private store = inject(Store);
  private emailService = inject(EmailService);
  private sseService = inject(SseService);
  private destroy$ = new Subject<void>();
  private selectedTeam$ = new BehaviorSubject<string | null>(null);

  selectedTeam: string | null = null;
  teamEmails$: Observable<Email[]>;
  selectedEmail: Email | null = null;
  chatMessage: string = '';
  directQuery: string = '';
  isSubmittingQuery: boolean = false;

  showDirectInteraction: boolean = false;
  showTeamPresentation: boolean = false;
  isEditMode: boolean = false;

  teams: { [key: string]: TeamInfo } = {
    'fraud': {
      name: 'Fraud Investigation Unit',
      key: 'fraud',
      badge: 'team-fraud',
      members: [
        {
          name: 'Fraud Detection Specialist',
          role: 'Identify suspicious patterns, transaction anomalies, and fraud indicators',
          icon: '🔍',
          memberType: 'Team Member',
          personality: 'Suspicious and investigative. Looks for red flags. Says \'I notice that...\' and \'This pattern suggests...\'',
          responsibilities: 'Identify suspicious patterns, transaction anomalies, and fraud indicators',
          communicationStyle: 'Skeptical, detail-focused, investigative'
        },
        {
          name: 'Forensic Analyst',
          role: 'Conduct technical analysis, trace transactions, analyze digital evidence',
          icon: '🧪',
          memberType: 'Team Member',
          personality: 'Technical and methodical. Deep dives into evidence. Uses phrases like \'The technical analysis shows...\' and \'Examining the metadata...\'',
          responsibilities: 'Conduct technical analysis, trace transactions, analyze digital evidence',
          communicationStyle: 'Technical, precise, methodical'
        },
        {
          name: 'Legal Advisor',
          role: 'Assess legal implications, regulatory requirements, evidence admissibility',
          icon: '⚖️',
          memberType: 'Team Member',
          personality: 'Cautious and procedural. Ensures compliance. Says \'From a legal standpoint...\' and \'We must ensure...\'',
          responsibilities: 'Assess legal implications, regulatory requirements, evidence admissibility',
          communicationStyle: 'Procedural, cautious, compliance-focused'
        },
        {
          name: 'Security Director',
          role: 'Decide on containment actions, client contact, law enforcement involvement',
          icon: '🛡️',
          memberType: 'Decision Maker',
          personality: 'Decisive and action-oriented. Makes containment decisions. Uses phrases like \'We need to immediately...\' and \'The priority is...\'',
          responsibilities: 'Decide on containment actions, client contact, law enforcement involvement',
          communicationStyle: 'Decisive, action-oriented, protective'
        }
      ]
    },
    'compliance': {
      name: 'Compliance & Regulatory Affairs',
      key: 'compliance',
      badge: 'team-compliance',
      members: [
        {
          name: 'Compliance Officer',
          role: 'Verify regulatory compliance, policy adherence, documentation requirements',
          icon: '📋',
          memberType: 'Team Member',
          personality: 'Rule-oriented and systematic. Checks regulations. Says \'According to regulation...\' and \'We must comply with...\'',
          responsibilities: 'Verify regulatory compliance, policy adherence, documentation requirements',
          communicationStyle: 'Systematic, rule-bound, thorough'
        },
        {
          name: 'Legal Counsel',
          role: 'Interpret regulations, assess legal risks, provide legal opinions',
          icon: '⚖️',
          memberType: 'Team Member',
          personality: 'Analytical and interpretive. Explains legal nuances. Uses phrases like \'The legal interpretation is...\' and \'From a liability perspective...\'',
          responsibilities: 'Interpret regulations, assess legal risks, provide legal opinions',
          communicationStyle: 'Analytical, interpretive, cautious'
        },
        {
          name: 'Auditor',
          role: 'Audit compliance processes, verify documentation, check audit trails',
          icon: '📊',
          memberType: 'Team Member',
          personality: 'Meticulous and verification-focused. Double-checks everything. Says \'Let me verify...\' and \'The audit trail shows...\'',
          responsibilities: 'Audit compliance processes, verify documentation, check audit trails',
          communicationStyle: 'Meticulous, verification-focused, detail-oriented'
        },
        {
          name: 'Regulatory Liaison',
          role: 'Determine reporting obligations, draft regulator communications, manage relationships',
          icon: '🏛️',
          memberType: 'Decision Maker',
          personality: 'Strategic and communicative. Manages regulator relationships. Uses phrases like \'Based on regulator expectations...\' and \'We should report...\'',
          responsibilities: 'Determine reporting obligations, draft regulator communications, manage relationships',
          communicationStyle: 'Strategic, communicative, proactive'
        }
      ]
    },
    'investments': {
      name: 'Investment Research Team',
      key: 'investments',
      badge: 'team-investments',
      members: [
        {
          name: 'Financial Analyst',
          role: 'Impress customers with financial data and market trends analysis',
          icon: '📊',
          memberType: 'Team Member',
          personality: 'Seasoned expert in stock market analysis. The Best Financial Analyst. Says \'The financial data shows...\' and \'Market trends indicate...\'',
          responsibilities: 'Impress customers with financial data and market trends analysis. Evaluate P/E ratio, EPS growth, revenue trends, and debt-to-equity metrics. Compare performance against industry peers.',
          communicationStyle: 'Expert, analytical, confident'
        },
        {
          name: 'Research Analyst',
          role: 'Excel at data gathering and interpretation',
          icon: '🔍',
          memberType: 'Team Member',
          personality: 'Known as the BEST research analyst. Skilled in sifting through news, company announcements, and market sentiments. Says \'The research shows...\' and \'Looking at recent developments...\'',
          responsibilities: 'Excel at data gathering and interpretation. Compile recent news, press releases, and market analyses. Highlight significant events and analyst perspectives.',
          communicationStyle: 'Thorough, investigative, detail-oriented'
        },
        {
          name: 'Filings Analyst',
          role: 'Review latest 10-Q and 10-K EDGAR filings',
          icon: '📋',
          memberType: 'Team Member',
          personality: 'Expert in analyzing SEC filings and regulatory documents. Says \'The filings reveal...\' and \'According to the 10-K...\'',
          responsibilities: 'Review latest 10-Q and 10-K EDGAR filings. Extract insights from Management Discussion & Analysis, financial statements, and risk factors.',
          communicationStyle: 'Meticulous, regulatory-focused, analytical'
        },
        {
          name: 'Investment Advisor',
          role: 'Deliver comprehensive stock analyses and strategic investment recommendations',
          icon: '💼',
          memberType: 'Decision Maker',
          personality: 'Experienced advisor combining analytical insights. Says \'Based on our comprehensive analysis...\' and \'My recommendation is...\'',
          responsibilities: 'Deliver comprehensive stock analyses and strategic investment recommendations. Synthesize all analyses into unified investment guidance.',
          communicationStyle: 'Authoritative, strategic, actionable'
        }
      ]
    }
  };

  private discussionMessages: { [emailId: number]: DiscussionMessage[] } = {};

  constructor() {
    // Combine selected team and emails observables
    this.teamEmails$ = combineLatest([
      this.store.select(selectAllEmails),
      this.selectedTeam$
    ]).pipe(
      map(([emails, team]) => this.filterEmailsByTeam(emails, team))
    );
  }

  ngOnInit(): void {
    // Load emails from store
    this.store.dispatch(EmailsActions.loadEmails({ limit: 100, offset: 0, append: false }));

    // Connect to SSE for real-time updates
    this.sseService.connect().pipe(
      takeUntil(this.destroy$)
    ).subscribe();

    // Listen for agentic workflow messages
    this.sseService.onEvent('agentic_message').pipe(
      takeUntil(this.destroy$)
    ).subscribe(data => {
      console.log('[SSE] Agentic message:', data);
      this.handleAgenticMessage(data);
    });

    // Listen for workflow completion
    this.sseService.onEvent('agentic_complete').pipe(
      takeUntil(this.destroy$)
    ).subscribe(data => {
      console.log('[SSE] Agentic complete:', data);
      this.handleAgenticComplete(data);
    });

    // Subscribe to route query parameters
    this.route.queryParams.pipe(
      takeUntil(this.destroy$)
    ).subscribe(params => {
      this.selectedTeam = params['team'] || null;
      this.selectedTeam$.next(this.selectedTeam);
      console.log('Selected team:', this.selectedTeam);

      // Check if email_id is provided in query params
      const emailId = params['email_id'];
      if (emailId) {
        // Wait for emails to load, then select the email
        this.store.select(selectAllEmails)
          .pipe(takeUntil(this.destroy$))
          .subscribe(emails => {
            const email = emails.find(e => e.id === parseInt(emailId, 10));
            if (email && this.selectedEmail?.id !== email.id) {
              console.log('[Query Params] Selecting email:', emailId);
              this.selectEmail(email);
            }
          });
      }

      // Show direct interaction and team presentation when team is selected
      this.updateViewState();
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.selectedTeam$.complete();
  }

  private filterEmailsByTeam(emails: Email[], team: string | null): Email[] {
    console.log('Filtering emails:', emails.length, 'Team:', team);

    if (!team || team === 'all') {
      // Show all emails with any team assignment
      const filtered = emails.filter(e => e.assigned_team).slice(0, 10);
      console.log('All teams - showing', filtered.length, 'emails');
      return filtered;
    }

    // Filter by specific team
    const filtered = emails.filter(e => e.assigned_team === team).slice(0, 10);
    console.log(`Team ${team} - showing`, filtered.length, 'emails');
    return filtered;
  }

  getCurrentTeamInfo(): TeamInfo | null {
    if (!this.selectedTeam || this.selectedTeam === 'all') {
      return null;
    }
    return this.teams[this.selectedTeam] || null;
  }

  getTeamName(teamKey: string): string {
    return this.teams[teamKey]?.name || teamKey;
  }

  selectEmail(email: Email): void {
    this.selectedEmail = email;
    this.updateViewState();

    // Load historical messages from workflow_results if available
    if (email && email.workflow_results && email.workflow_results.length > 0) {
      console.log(`[selectEmail] Email ${email.id} has ${email.workflow_results.length} workflow results`);

      const workflowResult = email.workflow_results[0];

      if (!workflowResult.result) {
        console.warn(`[selectEmail] No result field in workflow_result for email ${email.id}`);
        return;
      }

      if (!workflowResult.result.discussion) {
        console.warn(`[selectEmail] No discussion field in result for email ${email.id}`);
        return;
      }

      if (!workflowResult.result.discussion.messages) {
        console.warn(`[selectEmail] No messages array in discussion for email ${email.id}`);
        return;
      }

      // Convert workflow messages to discussion messages format
      this.discussionMessages[email.id] = workflowResult.result.discussion.messages.map((msg) => ({
        agentName: msg.role,
        agentIcon: msg.icon,
        content: msg.text,
        timestamp: msg.timestamp || 'Earlier',
        isToolUsage: msg.is_tool_usage || false  // Fixed: was incorrectly using is_decision
      }));

      console.log(`[selectEmail] Successfully loaded ${this.discussionMessages[email.id].length} historical messages for email ${email.id}`);
    } else {
      console.log(`[selectEmail] Email ${email.id} has no workflow results`);
    }
  }

  private updateViewState(): void {
    // Show direct interaction and team presentation when:
    // 1. A specific team is selected (not 'all')
    // 2. No email is currently selected
    const hasSpecificTeam = !!(this.selectedTeam && this.selectedTeam !== 'all');
    const noEmailSelected = !this.selectedEmail;

    this.showDirectInteraction = hasSpecificTeam && noEmailSelected;
    this.showTeamPresentation = hasSpecificTeam && noEmailSelected;
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) {
      return `${diffMins} min ago`;
    } else if (diffMins < 1440) {
      return `${Math.floor(diffMins / 60)} hr ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  getTeamColor(team?: string): string {
    const colors: { [key: string]: string } = {
      'fraud': '#ffebee',
      'compliance': '#f3e5f5',
      'investments': '#e8f5e9',
      'default': '#f5f5f5'
    };
    return colors[team || 'default'] || colors['default'];
  }

  getProgressPercent(email: Email): number {
    if (!email.processed) return 0;
    if (email.workflow_results && email.workflow_results.length > 0) return 100;
    return 50;
  }

  getEmailDiscussion(emailId: number): DiscussionMessage[] {
    return this.discussionMessages[emailId] || [];
  }

  sendChatMessage(): void {
    if (!this.chatMessage.trim() || !this.selectedEmail) return;

    // Add user message to discussion
    const userMessage: DiscussionMessage = {
      agentName: 'You',
      agentIcon: '👤',
      content: this.chatMessage,
      timestamp: 'Just now'
    };

    if (!this.discussionMessages[this.selectedEmail.id]) {
      this.discussionMessages[this.selectedEmail.id] = [];
    }

    this.discussionMessages[this.selectedEmail.id].push(userMessage);

    // Mock AI response
    setTimeout(() => {
      if (this.selectedEmail) {
        const aiResponse: DiscussionMessage = {
          agentName: 'AI Coordinator',
          agentIcon: '🤖',
          content: 'Thank you for your question. The team is analyzing this...',
          timestamp: 'Just now'
        };
        this.discussionMessages[this.selectedEmail.id].push(aiResponse);
      }
    }, 1000);

    this.chatMessage = '';
  }

  handleChatKeypress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendChatMessage();
    }
  }

  submitDirectQuery(): void {
    const query = this.directQuery.trim();

    if (!query) {
      return;
    }

    if (!this.selectedTeam || this.selectedTeam === 'all') {
      return;
    }

    // Show loading state
    this.isSubmittingQuery = true;

    // Call API to create direct query task
    this.emailService.submitDirectQuery(this.selectedTeam, query)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (result) => {
          console.log('[Direct Query] Task created:', result.task_id, 'Email:', result.email_id);

          // Clear query input
          this.directQuery = '';
          this.isSubmittingQuery = false;

          // Reload emails to get the newly created task email
          this.store.dispatch(EmailsActions.loadEmails({ limit: 100, offset: 0, append: false }));

          // Wait a bit for store to update, then select the email
          setTimeout(() => {
            // Find and select the email by ID
            this.store.select(selectAllEmails)
              .pipe(takeUntil(this.destroy$))
              .subscribe(emails => {
                const email = emails.find(e => e.id === result.email_id);
                if (email) {
                  this.selectEmail(email);
                  console.log('[Direct Query] Selected email:', email.id);
                }
              });
          }, 500);
        },
        error: (error) => {
          console.error('[Direct Query] Error:', error);
          this.isSubmittingQuery = false;
        }
      });
  }

  clearDirectQuery(): void {
    this.directQuery = '';
  }

  enterEditMode(): void {
    if (!this.selectedTeam || this.selectedTeam === 'all') {
      return;
    }

    const teamInfo = this.getCurrentTeamInfo();
    if (!teamInfo) {
      return;
    }

    // Switch to edit mode
    this.isEditMode = true;
    this.showTeamPresentation = false;
  }

  exitEditMode(): void {
    // Switch back to presentation mode
    this.isEditMode = false;
    this.showTeamPresentation = true;
  }

  getStatusText(email: Email): string {
    if (!email.processed) return 'Pending';
    if (email.workflow_results && email.workflow_results.length > 0) return 'Completed';
    return 'Processing';
  }

  getStatusClass(email: Email): string {
    if (!email.processed) return 'status-pending';
    if (email.workflow_results && email.workflow_results.length > 0) return 'status-completed';
    return 'status-processing';
  }

  getQueryHint(): string {
    if (this.selectedTeam === 'investments') {
      return 'For Investment Team: Request stock analysis by company name or ticker symbol (e.g., "Analyze Apple stock" or "Complete analysis for TSLA")';
    } else if (this.selectedTeam === 'fraud') {
      return 'For Fraud Team: Report suspicious activities (e.g., "Investigate unusual transaction pattern")';
    } else if (this.selectedTeam === 'compliance') {
      return 'For Compliance Team: Submit regulatory queries (e.g., "Review FATCA compliance requirements")';
    }
    return 'Submit your request to the team';
  }

  private handleAgenticMessage(data: any): void {
    const emailId = data.email_id;
    const agentName = data.agent_name || 'Agent';
    const message = data.message || '';

    if (!emailId) return;

    // Add message to discussion
    if (!this.discussionMessages[emailId]) {
      this.discussionMessages[emailId] = [];
    }

    const newMessage: DiscussionMessage = {
      agentName: agentName,
      agentIcon: this.getAgentIcon(agentName),
      content: message,
      timestamp: 'Just now',
      isToolUsage: data.tool_usage || false
    };

    this.discussionMessages[emailId].push(newMessage);
  }

  private handleAgenticComplete(data: any): void {
    const emailId = data.email_id;
    console.log('[Workflow Complete] Email:', emailId);

    // Reload emails to get updated status
    this.store.dispatch(EmailsActions.loadEmails({ limit: 100, offset: 0, append: false }));
  }

  private getAgentIcon(agentName: string): string {
    const iconMap: { [key: string]: string } = {
      'Financial Analyst': '📊',
      'Research Analyst': '🔍',
      'Filings Analyst': '📋',
      'Investment Advisor': '💼',
      'Fraud Detection Specialist': '🔍',
      'Forensic Analyst': '🧪',
      'Legal Advisor': '⚖️',
      'Security Director': '🛡️',
      'Compliance Officer': '📋',
      'Legal Counsel': '⚖️',
      'Auditor': '📊',
      'Regulatory Liaison': '🏛️'
    };
    return iconMap[agentName] || '🤖';
  }
}
