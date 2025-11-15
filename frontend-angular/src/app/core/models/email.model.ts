export interface Email {
  id: number;
  subject: string;
  sender: string;
  recipient: string;
  body?: string;  // Legacy field for compatibility
  body_text?: string;  // Actual field from API
  body_html?: string;  // HTML version from API
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
  team_assigned_at?: string | null;
  agentic_task_id?: string | null;
  badges: string[];
  ui_badges: string[];
  workflow_results: WorkflowResult[];
  llm_analysis?: LLMAnalysis;
  enriched_data?: EnrichedData;
  summary?: string | null;
  call_to_actions?: string[];
  quick_reply_drafts?: QuickReplyDrafts;
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

export interface EnrichedData {
  enriched_keywords?: EnrichedKeyword[];
  relevant_pages?: string[];
  sender_employee?: EmployeeInfo;
  recipient_employee?: EmployeeInfo;
}

export interface EnrichedKeyword {
  keyword: string;
  wiki_page: string;
  confidence: number;
  context: string;
}

export interface EmployeeInfo {
  employee_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  mobile: string;
  department: string;
  designation: string;
  city: string;
  country: string;
}

export interface QuickReplyDrafts {
  formal?: string;
  friendly?: string;
  brief?: string;
}
