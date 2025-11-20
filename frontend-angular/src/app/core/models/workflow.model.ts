export interface AgenticTask {
  task_id: string;
  email_id: number;
  team: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  result?: AgenticResult;
}

export interface AgenticResult {
  status: string;
  email_id: number;
  team: string;
  team_name: string;
  discussion: Discussion;
}

export interface Discussion {
  messages: Message[];
  decision?: any;
  rounds?: number;
  fraud_analysis?: any;
}

export interface Message {
  role: string;
  icon: string;
  text: string;
  timestamp: string;
  is_thinking?: boolean;
  is_tool_usage?: boolean;
  is_decision?: boolean;
  tool_name?: string;
  tool_type?: string;
}

export interface ProgressUpdate {
  type: string;
  task_id?: string;
  message?: Message;
  status?: string;
  data?: any;
}

export interface FraudAnalysis {
  fraud_type: string;
  analysis: string;
  fraud_type_detection: FraudDetection;
  doer_checker_applied: boolean;
  debate_applied: boolean;
  iterations: number;
  collaboration_summary?: any;
}

export interface FraudDetection {
  fraud_type: string;
  confidence: 'LOW' | 'MEDIUM' | 'HIGH';
  urgency: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  summary: string;
  indicators: string[];
}

export interface Team {
  key: string;
  name: string;
  description: string;
  icon: string;
  agents: Agent[];
}

export interface Agent {
  role: string;
  icon: string;
  personality: string;
  responsibilities: string;
  style: string;
}
