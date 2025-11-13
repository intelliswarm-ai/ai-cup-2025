import { createFeatureSelector, createSelector } from '@ngrx/store';
import { StatisticsState } from './statistics.reducer';

// Feature selector
export const selectStatisticsState = createFeatureSelector<StatisticsState>('statistics');

// Selectors
export const selectStatistics = createSelector(
  selectStatisticsState,
  (state) => state.data
);

export const selectStatisticsLoading = createSelector(
  selectStatisticsState,
  (state) => state.loading
);

export const selectStatisticsError = createSelector(
  selectStatisticsState,
  (state) => state.error
);

export const selectStatisticsLastUpdated = createSelector(
  selectStatisticsState,
  (state) => state.lastUpdated
);

// Computed selectors
export const selectTotalEmails = createSelector(
  selectStatistics,
  (statistics) => statistics?.total_emails || 0
);

export const selectUnreadCount = createSelector(
  selectStatistics,
  (statistics) => statistics?.unprocessed_emails || statistics?.unread_count || 0
);

export const selectPhishingCount = createSelector(
  selectStatistics,
  (statistics) => statistics?.phishing_detected || statistics?.phishing_count || 0
);

export const selectSpamCount = createSelector(
  selectStatistics,
  (statistics) => statistics?.spam_count || 0
);

export const selectLegitimateCount = createSelector(
  selectStatistics,
  (statistics) => statistics?.legitimate_emails || statistics?.legitimate_count || 0
);

export const selectFraudDetected = createSelector(
  selectStatistics,
  (statistics) => statistics?.badge_counts?.RISK || statistics?.fraud_detected || 0
);
