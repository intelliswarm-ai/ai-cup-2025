export interface Email {
  id: number;
  subject: string;
  sender: string;
  recipient: string;
  body: string;
  received_at: string;
  processed: boolean;
  is_phishing: boolean;
  llm_processed: boolean;
  enriched: boolean;
  wiki_enriched: boolean;
  phone_enriched: boolean;
  label: number | null;
  phishing_type: string | null;
  suggested_team: string | null;
  assigned_team: string | null;
  badges: string[];
  ui_badges: string[];
  workflow_results: WorkflowResult[];
  llm_analysis?: LLMAnalysis;
}

export interface WorkflowResult {
  id: number;
  workflow_name: string;
  is_phishing_detected: boolean;
  confidence_score: number;
  risk_indicators: string[];
  created_at: string;
}

export interface LLMAnalysis {
  message_anatomy?: {
    purpose?: string;
    key_entities?: string[];
    urgency_level?: string;
    action_required?: string;
  };
  enrichment?: {
    wiki_data?: any;
    phone_data?: any;
  };
}

export interface EmailFilters {
  search?: string;
  showProcessed?: boolean;
  showUnprocessed?: boolean;
  showPhishing?: boolean;
  showLegitimate?: boolean;
  team?: string;
}

export interface EmailsState {
  emails: Email[];
  selectedEmail: Email | null;
  loading: boolean;
  error: any;
  currentOffset: number;
  hasMore: boolean;
  filters: EmailFilters;
}

export interface TeamAssignment {
  emailId: number;
  team: string;
  message?: string;
}
