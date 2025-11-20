import { createReducer, on } from '@ngrx/store';
import { Statistics } from '../../core/models';
import * as StatisticsActions from './statistics.actions';

export interface StatisticsState {
  data: Statistics | null;
  loading: boolean;
  error: any;
  lastUpdated: string | null;
}

export const initialState: StatisticsState = {
  data: null,
  loading: false,
  error: null,
  lastUpdated: null
};

export const statisticsReducer = createReducer(
  initialState,

  // Load Statistics
  on(StatisticsActions.loadStatistics, (state) => ({
    ...state,
    loading: true,
    error: null
  })),

  on(StatisticsActions.loadStatisticsSuccess, (state, { statistics }) => ({
    ...state,
    data: statistics,
    loading: false,
    error: null,
    lastUpdated: new Date().toISOString()
  })),

  on(StatisticsActions.loadStatisticsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error
  })),

  // Update Statistics
  on(StatisticsActions.updateStatistics, (state, { statistics }) => ({
    ...state,
    data: state.data ? { ...state.data, ...statistics } : null,
    lastUpdated: new Date().toISOString()
  })),

  // Reset Statistics
  on(StatisticsActions.resetStatistics, () => initialState)
);
