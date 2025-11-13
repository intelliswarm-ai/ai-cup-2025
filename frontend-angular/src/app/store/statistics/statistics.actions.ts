import { createAction, props } from '@ngrx/store';
import { Statistics } from '../../core/models';

// Load Statistics
export const loadStatistics = createAction(
  '[Statistics] Load Statistics'
);

export const loadStatisticsSuccess = createAction(
  '[Statistics] Load Statistics Success',
  props<{ statistics: Statistics }>()
);

export const loadStatisticsFailure = createAction(
  '[Statistics] Load Statistics Failure',
  props<{ error: any }>()
);

// Update Statistics (from SSE)
export const updateStatistics = createAction(
  '[Statistics] Update Statistics',
  props<{ statistics: Partial<Statistics> }>()
);

// Reset Statistics
export const resetStatistics = createAction(
  '[Statistics] Reset Statistics'
);
