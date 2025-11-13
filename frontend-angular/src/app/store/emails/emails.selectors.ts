import { createFeatureSelector, createSelector } from '@ngrx/store';
import { EmailsState } from '../../core/models/email.model';

export const selectEmailsState = createFeatureSelector<EmailsState>('emails');

export const selectAllEmails = createSelector(
  selectEmailsState,
  (state) => state.emails
);

export const selectSelectedEmail = createSelector(
  selectEmailsState,
  (state) => state.selectedEmail
);

export const selectEmailsLoading = createSelector(
  selectEmailsState,
  (state) => state.loading
);

export const selectEmailsError = createSelector(
  selectEmailsState,
  (state) => state.error
);

export const selectHasMoreEmails = createSelector(
  selectEmailsState,
  (state) => state.hasMore
);

export const selectCurrentOffset = createSelector(
  selectEmailsState,
  (state) => state.currentOffset
);

export const selectEmailsCount = createSelector(
  selectAllEmails,
  (emails) => emails.length
);

export const selectProcessedEmails = createSelector(
  selectAllEmails,
  (emails) => emails.filter(e => e.processed)
);

export const selectPhishingEmails = createSelector(
  selectAllEmails,
  (emails) => emails.filter(e => e.is_phishing)
);
