import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Email, TeamAssignment } from '../../../../core/models/email.model';
import { Router } from '@angular/router';
import { SseService } from '../../../../core/services/sse.service';
import { Subject, takeUntil } from 'rxjs';

interface ProgressStep {
  icon: string;
  label: string;
  status: 'pending' | 'active' | 'completed';
  agent: string;
}

interface AnalysisMessage {
  icon: string;
  agentName: string;
  timestamp: string;
  content: string;
}

@Component({
  selector: 'app-email-detail-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './email-detail-modal.component.html',
  styleUrl: './email-detail-modal.component.scss'
})
export class EmailDetailModalComponent implements OnInit, OnDestroy {
  @Input() email: Email | null = null;
  @Input() isOpen = false;
  @Output() closeModal = new EventEmitter<void>();
  @Output() processEmail = new EventEmitter<number>();
  @Output() assignToTeam = new EventEmitter<TeamAssignment>();

  private destroy$ = new Subject<void>();

  // Fraud progress tracking
  showFraudProgress = false;
  fraudProgressSteps: ProgressStep[] = [
    { icon: '🔍', label: 'Fraud Type Detection', status: 'pending', agent: 'Fraud Investigation Unit' },
    { icon: '🎣', label: 'Deep Investigation', status: 'pending', agent: 'Phishing Analysis' },
    { icon: '💾', label: 'Historical Analysis', status: 'pending', agent: 'Database Investigation' },
    { icon: '⚖️', label: 'Risk Assessment', status: 'pending', agent: 'Final Decision' }
  ];
  fraudProgressPercent = 0;
  fraudMessages: AnalysisMessage[] = [];

  constructor(
    private router: Router,
    private sseService: SseService
  ) {}

  ngOnInit(): void {
    // Ensure SSE is connected (idempotent - won't reconnect if already connected)
    if (!this.sseService.connected) {
      this.sseService.connect().pipe(
        takeUntil(this.destroy$)
      ).subscribe();
    }

    // Subscribe to SSE events for real-time updates
    this.subscribeToSSE();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private subscribeToSSE(): void {
    // Listen for agentic progress events
    this.sseService.onEvent('agentic_progress').pipe(
      takeUntil(this.destroy$)
    ).subscribe((data: any) => {
      console.log('[EmailDetailModal] Received agentic_progress:', data);
      if (this.email && data.email_id === this.email.id && data.team === 'fraud') {
        this.updateFraudProgress(data);
      }
    });

    // Listen for agentic messages
    this.sseService.onEvent('agentic_message').pipe(
      takeUntil(this.destroy$)
    ).subscribe((data: any) => {
      console.log('[EmailDetailModal] Received agentic_message:', data);
      if (this.email && data.email_id === this.email.id && data.team === 'fraud') {
        this.addFraudMessage(data);
      }
    });
  }

  private updateFraudProgress(data: any): void {
    const { agent, status, step } = data;

    // Update step status based on agent
    this.fraudProgressSteps.forEach((progressStep, index) => {
      if (progressStep.agent === agent || index === step) {
        progressStep.status = status;
      }
    });

    // Calculate progress percentage
    const completedSteps = this.fraudProgressSteps.filter(s => s.status === 'completed').length;
    const totalSteps = this.fraudProgressSteps.length;
    this.fraudProgressPercent = (completedSteps / totalSteps) * 100;
  }

  private addFraudMessage(data: any): void {
    const message: AnalysisMessage = {
      icon: this.getAgentIcon(data.agent || data.role),
      agentName: data.agent || data.role || 'System',
      timestamp: new Date().toLocaleTimeString(),
      content: data.message || data.text || ''
    };

    this.fraudMessages.push(message);
  }

  private getAgentIcon(agentName: string): string {
    const icons: { [key: string]: string } = {
      'Database Investigation Agent': '💾',
      'Phishing Analysis Specialist': '🔨',
      'Fraud Investigation Unit': '🔍',
      'Risk Assessment Agent': '⚖️'
    };
    return icons[agentName] || '🤖';
  }

  close(): void {
    this.closeModal.emit();
  }

  getStatusBadgeClass(): string {
    if (!this.email) return '';
    if (!this.email.processed) return 'bg-gradient-warning';
    return this.email.is_phishing ? 'bg-gradient-danger' : 'bg-gradient-success';
  }

  getStatusText(): string {
    if (!this.email) return '';
    if (!this.email.processed) return 'Pending Analysis';
    return this.email.is_phishing ? 'Phishing' : 'Legitimate';
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }

  getBadgeIcon(badgeType: string): string {
    const icons: { [key: string]: string } = {
      'MEETING': 'event',
      'RISK': 'shield',
      'EXTERNAL': 'close',
      'AUTOMATED': 'settings',
      'VIP': 'star',
      'FOLLOW_UP': 'refresh',
      'NEWSLETTER': 'mail',
      'FINANCE': 'attach_money'
    };
    return icons[badgeType] || 'label';
  }

  getTeamDisplayName(teamKey: string): string {
    const teamNames: { [key: string]: string } = {
      'fraud': 'Fraud Investigation',
      'compliance': 'Compliance',
      'investments': 'Investment Team'
    };
    return teamNames[teamKey] || teamKey;
  }

  runAnalysis(): void {
    if (this.email) {
      this.processEmail.emit(this.email.id);
    }
  }

  viewTeamDiscussion(): void {
    if (this.email?.agentic_task_id) {
      // Navigate to agentic-teams page with task_id and email_id
      this.router.navigate(['/agentic-teams'], {
        queryParams: {
          email_id: this.email.id,
          task_id: this.email.agentic_task_id
        }
      });
      this.close();
    }
  }

  assignTeam(team: string): void {
    if (this.email) {
      console.log(`[EmailDetailModal] Assigning email ${this.email.id} to team: ${team}`);

      // Show fraud progress tracker if fraud team is selected
      if (team === 'fraud') {
        console.log('[EmailDetailModal] Showing fraud progress tracker');
        this.showFraudProgress = true;
        this.fraudMessages = [];
        this.fraudProgressSteps.forEach(step => step.status = 'pending');
        this.fraudProgressPercent = 0;
      }

      // Assign to team without popups
      this.assignToTeam.emit({
        emailId: this.email.id,
        team,
        message: undefined  // Can be enhanced later with a proper modal form
      });

      // Don't close modal if showing fraud progress - let user watch the analysis
      if (team !== 'fraud') {
        this.close();
      }
    }
  }
}
