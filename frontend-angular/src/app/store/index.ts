import { ActionReducerMap } from '@ngrx/store';
import { statisticsReducer, StatisticsState } from './statistics/statistics.reducer';
import { emailsReducer } from './emails/emails.reducer';
import { EmailsState } from '../core/models/email.model';

// Root state interface
export interface AppState {
  statistics: StatisticsState;
  emails: EmailsState;
  // Will add more feature states as we migrate:
  // workflows: WorkflowsState;
}

// Root reducers
export const reducers: ActionReducerMap<AppState> = {
  statistics: statisticsReducer,
  emails: emailsReducer
  // Will add more reducers:
  // workflows: workflowsReducer
};

// Export all selectors for easy access
export * from './statistics/statistics.selectors';
export * from './emails/emails.selectors';
// export * from './workflows/workflows.selectors';
