import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Email, TeamAssignment } from '../../../../core/models/email.model';
import { Router } from '@angular/router';

@Component({
  selector: 'app-email-detail-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './email-detail-modal.component.html',
  styleUrl: './email-detail-modal.component.scss'
})
export class EmailDetailModalComponent {
  @Input() email: Email | null = null;
  @Input() isOpen = false;
  @Output() closeModal = new EventEmitter<void>();
  @Output() processEmail = new EventEmitter<number>();
  @Output() assignToTeam = new EventEmitter<TeamAssignment>();

  constructor(private router: Router) {}

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
      // Assign to team without popups
      this.assignToTeam.emit({
        emailId: this.email.id,
        team,
        message: undefined  // Can be enhanced later with a proper modal form
      });

      // Close modal - the parent will handle navigation to agentic-teams page
      this.close();
    }
  }
}
