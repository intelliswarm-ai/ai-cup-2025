import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { Email } from '../../core/models/email.model';
import { Statistics } from '../../core/models';
import {
  selectAllEmails,
  selectEmailsLoading,
  selectHasMoreEmails,
  selectStatistics,
  selectTotalEmails,
  selectPhishingCount,
  selectSelectedEmail
} from '../../store';
import * as EmailsActions from '../../store/emails/emails.actions';
import * as StatisticsActions from '../../store/statistics/statistics.actions';
import { StatsCardComponent } from '../dashboard/components/stats-card.component';
import { EmailDetailModalComponent } from './components/email-detail-modal/email-detail-modal.component';

@Component({
  selector: 'app-mailbox',
  standalone: true,
  imports: [CommonModule, StatsCardComponent, EmailDetailModalComponent],
  templateUrl: './mailbox.component.html',
  styleUrl: './mailbox.component.scss'
})
export class MailboxComponent implements OnInit {
  private store = inject(Store);

  // Observable streams
  emails$: Observable<Email[]>;
  loading$: Observable<boolean>;
  hasMore$: Observable<boolean>;
  statistics$: Observable<Statistics | null>;
  totalEmails$: Observable<number>;
  phishingCount$: Observable<number>;
  selectedEmail$: Observable<Email | null>;

  // Modal state
  isModalOpen = false;

  constructor() {
    this.emails$ = this.store.select(selectAllEmails);
    this.loading$ = this.store.select(selectEmailsLoading);
    this.hasMore$ = this.store.select(selectHasMoreEmails);
    this.statistics$ = this.store.select(selectStatistics);
    this.totalEmails$ = this.store.select(selectTotalEmails);
    this.phishingCount$ = this.store.select(selectPhishingCount);
    this.selectedEmail$ = this.store.select(selectSelectedEmail);
  }

  ngOnInit(): void {
    // Load statistics and emails
    this.store.dispatch(StatisticsActions.loadStatistics());
    this.store.dispatch(EmailsActions.loadEmails({ limit: 50, offset: 0, append: false }));
  }

  fetchEmails(): void {
    this.store.dispatch(EmailsActions.fetchEmailsFromMailpit());
  }

  processAll(): void {
    this.store.dispatch(EmailsActions.processAllEmails());
  }

  refresh(): void {
    this.store.dispatch(EmailsActions.clearEmails());
    this.store.dispatch(StatisticsActions.loadStatistics());
    this.store.dispatch(EmailsActions.loadEmails({ limit: 50, offset: 0, append: false }));
  }

  viewEmail(email: Email): void {
    this.store.dispatch(EmailsActions.selectEmail({ email }));
    this.isModalOpen = true;
  }

  closeModal(): void {
    this.isModalOpen = false;
    this.store.dispatch(EmailsActions.selectEmail({ email: null }));
  }

  getStatusBadgeClass(email: Email): string {
    if (!email.processed) return 'pending-badge';
    return email.is_phishing ? 'phishing-badge' : 'safe-badge';
  }

  getStatusText(email: Email): string {
    if (!email.processed) return 'Pending';
    return email.is_phishing ? 'Phishing' : 'Safe';
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
}
