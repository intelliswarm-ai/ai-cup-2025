import { createReducer, on } from '@ngrx/store';
import * as EmailsActions from './emails.actions';
import { EmailsState } from '../../core/models/email.model';

export const initialState: EmailsState = {
  emails: [],
  selectedEmail: null,
  loading: false,
  error: null,
  currentOffset: 0,
  hasMore: true,
  filters: {}
};

export const emailsReducer = createReducer(
  initialState,
  
  // Load emails
  on(EmailsActions.loadEmails, state => ({
    ...state,
    loading: true,
    error: null
  })),
  on(EmailsActions.loadEmailsSuccess, (state, { emails, append }) => ({
    ...state,
    emails: append ? [...state.emails, ...emails] : emails,
    loading: false,
    error: null,
    currentOffset: append ? state.currentOffset + emails.length : emails.length,
    hasMore: emails.length === 50
  })),
  on(EmailsActions.loadEmailsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error
  })),
  
  // Load single email
  on(EmailsActions.loadEmailSuccess, (state, { email }) => {
    // Update email in list if it exists
    const emails = state.emails.map(e => e.id === email.id ? email : e);
    return {
      ...state,
      emails,
      selectedEmail: email,
      loading: false
    };
  }),
  
  // Select email
  on(EmailsActions.selectEmail, (state, { email }) => ({
    ...state,
    selectedEmail: email
  })),
  
  // Fetch from MailPit
  on(EmailsActions.fetchEmailsFromMailpit, state => ({
    ...state,
    loading: true
  })),
  on(EmailsActions.fetchEmailsFromMailpitSuccess, state => ({
    ...state,
    loading: false
  })),
  on(EmailsActions.fetchEmailsFromMailpitFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error
  })),
  
  // Process all
  on(EmailsActions.processAllEmails, state => ({
    ...state,
    loading: true
  })),
  on(EmailsActions.processAllEmailsSuccess, state => ({
    ...state,
    loading: false
  })),
  on(EmailsActions.processAllEmailsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error
  })),
  
  // Assign team
  on(EmailsActions.assignTeamSuccess, (state, { email }) => {
    const emails = state.emails.map(e => e.id === email.id ? email : e);
    return {
      ...state,
      emails,
      selectedEmail: state.selectedEmail?.id === email.id ? email : state.selectedEmail
    };
  }),
  
  // Clear
  on(EmailsActions.clearEmails, state => initialState)
);
