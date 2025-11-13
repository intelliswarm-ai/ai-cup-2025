import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Email } from '../../../../core/models/email.model';

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
    return this.email.is_phishing ? 'Phishing Detected' : 'Legitimate';
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
}
