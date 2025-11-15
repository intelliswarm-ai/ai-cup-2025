import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Email } from '../../../../core/models/email.model';
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
  @Output() assignToTeam = new EventEmitter<{ emailId: number; team: string }>();

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
      // Show confirmation with option for message
      const message = prompt(
        `Assign this email to ${this.getTeamDisplayName(team)} team?\n\n` +
        `Email: ${this.email.subject}\n\n` +
        `Optional: Add specific instructions or questions for the team:`,
        ''
      );

      // null means cancelled, empty string means no message (but confirmed)
      if (message !== null) {
        this.assignToTeam.emit({
          emailId: this.email.id,
          team,
          message: message.trim() || undefined
        });

        // Show immediate feedback
        alert(`Email assigned to ${this.getTeamDisplayName(team)} team!\nAgentic workflow will start processing this email.`);

        // Close modal after assignment
        this.close();
      }
    }
  }
}
