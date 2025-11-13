import { createAction, props } from '@ngrx/store';
import { Email, TeamAssignment } from '../../core/models/email.model';

// Load emails
export const loadEmails = createAction(
  '[Emails] Load Emails',
  props<{ limit?: number; offset?: number; append?: boolean }>()
);

export const loadEmailsSuccess = createAction(
  '[Emails] Load Emails Success',
  props<{ emails: Email[]; append: boolean }>()
);

export const loadEmailsFailure = createAction(
  '[Emails] Load Emails Failure',
  props<{ error: any }>()
);

// Load single email
export const loadEmail = createAction(
  '[Emails] Load Email',
  props<{ id: number }>()
);

export const loadEmailSuccess = createAction(
  '[Emails] Load Email Success',
  props<{ email: Email }>()
);

// Select email
export const selectEmail = createAction(
  '[Emails] Select Email',
  props<{ email: Email | null }>()
);

// Fetch from MailPit
export const fetchEmailsFromMailpit = createAction('[Emails] Fetch From MailPit');

export const fetchEmailsFromMailpitSuccess = createAction(
  '[Emails] Fetch From MailPit Success',
  props<{ fetched: number; total: number }>()
);

export const fetchEmailsFromMailpitFailure = createAction(
  '[Emails] Fetch From MailPit Failure',
  props<{ error: any }>()
);

// Process all emails
export const processAllEmails = createAction('[Emails] Process All');

export const processAllEmailsSuccess = createAction(
  '[Emails] Process All Success',
  props<{ count: number }>()
);

export const processAllEmailsFailure = createAction(
  '[Emails] Process All Failure',
  props<{ error: any }>()
);

// Assign team
export const assignTeam = createAction(
  '[Emails] Assign Team',
  props<{ assignment: TeamAssignment }>()
);

export const assignTeamSuccess = createAction(
  '[Emails] Assign Team Success',
  props<{ email: Email }>()
);

export const assignTeamFailure = createAction(
  '[Emails] Assign Team Failure',
  props<{ error: any }>()
);

// Clear emails
export const clearEmails = createAction('[Emails] Clear Emails');
