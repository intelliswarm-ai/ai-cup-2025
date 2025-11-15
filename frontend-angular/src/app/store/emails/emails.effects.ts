import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { map, catchError, switchMap, tap } from 'rxjs/operators';
import * as EmailsActions from './emails.actions';
import { EmailService } from '../../core/services/email.service';

export const loadEmails = createEffect(
  (actions$ = inject(Actions), emailService = inject(EmailService)) => {
    return actions$.pipe(
      ofType(EmailsActions.loadEmails),
      switchMap(({ limit = 50, offset = 0, append = false }) =>
        emailService.getEmails(limit, offset).pipe(
          map(emails => EmailsActions.loadEmailsSuccess({ emails, append })),
          catchError(error => of(EmailsActions.loadEmailsFailure({ error })))
        )
      )
    );
  },
  { functional: true }
);

export const loadEmail = createEffect(
  (actions$ = inject(Actions), emailService = inject(EmailService)) => {
    return actions$.pipe(
      ofType(EmailsActions.loadEmail),
      switchMap(({ id }) =>
        emailService.getEmailById(id).pipe(
          map(email => EmailsActions.loadEmailSuccess({ email })),
          catchError(error => of(EmailsActions.loadEmailsFailure({ error })))
        )
      )
    );
  },
  { functional: true }
);

export const fetchEmailsFromMailpit = createEffect(
  (actions$ = inject(Actions), emailService = inject(EmailService)) => {
    return actions$.pipe(
      ofType(EmailsActions.fetchEmailsFromMailpit),
      switchMap(() =>
        emailService.fetchEmailsFromMailpit().pipe(
          map(result => EmailsActions.fetchEmailsFromMailpitSuccess({ fetched: result.fetched, total: result.total_in_mailpit })),
          catchError(error => of(EmailsActions.fetchEmailsFromMailpitFailure({ error })))
        )
      )
    );
  },
  { functional: true }
);

export const fetchEmailsFromMailpitSuccess = createEffect(
  (actions$ = inject(Actions)) => {
    return actions$.pipe(
      ofType(EmailsActions.fetchEmailsFromMailpitSuccess),
      map(() => EmailsActions.loadEmails({ limit: 50, offset: 0, append: false }))
    );
  },
  { functional: true }
);

export const processAllEmails = createEffect(
  (actions$ = inject(Actions), emailService = inject(EmailService)) => {
    return actions$.pipe(
      ofType(EmailsActions.processAllEmails),
      switchMap(() =>
        emailService.processAllEmails().pipe(
          map(result => EmailsActions.processAllEmailsSuccess({ count: result.count })),
          catchError(error => of(EmailsActions.processAllEmailsFailure({ error })))
        )
      )
    );
  },
  { functional: true }
);

export const assignTeam = createEffect(
  (actions$ = inject(Actions), emailService = inject(EmailService)) => {
    return actions$.pipe(
      ofType(EmailsActions.assignTeam),
      switchMap(({ assignment }) =>
        emailService.assignTeamToEmail(assignment).pipe(
          map(response => EmailsActions.assignTeamSuccess({
            emailId: response.email_id,
            taskId: response.task_id,
            assignedTeam: response.assigned_team
          })),
          catchError(error => of(EmailsActions.assignTeamFailure({ error })))
        )
      )
    );
  },
  { functional: true }
);

export const navigateToAgenticTeamsAfterAssignment = createEffect(
  (actions$ = inject(Actions), router = inject(Router)) => {
    return actions$.pipe(
      ofType(EmailsActions.assignTeamSuccess),
      tap(({ emailId, taskId }) => {
        // Navigate to agentic-teams page to show real-time workflow discussion
        router.navigate(['/agentic-teams'], {
          queryParams: {
            email_id: emailId,
            task_id: taskId
          }
        });
      })
    );
  },
  { functional: true, dispatch: false }
);

export const reloadEmailsAfterAssignment = createEffect(
  (actions$ = inject(Actions)) => {
    return actions$.pipe(
      ofType(EmailsActions.assignTeamSuccess),
      map(() => EmailsActions.loadEmails({ limit: 100, offset: 0, append: false }))
    );
  },
  { functional: true }
);
