export interface Statistics {
  total_emails: number;
  processed_emails?: number;
  unprocessed_emails?: number;
  phishing_detected?: number;
  legitimate_emails?: number;
  phishing_percentage?: number;
  llm_processed?: number;
  badge_counts?: BadgeCounts;
  // Legacy fields for compatibility
  unread_count?: number;
  phishing_count?: number;
  spam_count?: number;
  legitimate_count?: number;
  fraud_detected?: number;
  investment_queries?: number;
  compliance_reviews?: number;
  avg_processing_time?: number;
  recent_activity?: Activity[];
}

export interface BadgeCounts {
  MEETING?: number;
  RISK?: number;
  EXTERNAL?: number;
  AUTOMATED?: number;
  VIP?: number;
  FOLLOW_UP?: number;
  NEWSLETTER?: number;
  FINANCE?: number;
}

export interface Activity {
  id: number;
  type: string;
  description: string;
  timestamp: string;
  email_id?: number;
  team?: string;
}

export interface ChartData {
  labels: string[];
  datasets: Dataset[];
}

export interface Dataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
}
