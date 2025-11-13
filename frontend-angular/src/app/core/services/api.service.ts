import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Email,
  Statistics
} from '../models';

// TODO: Add these types when needed
interface EmailListResponse {
  emails: Email[];
  total: number;
}

interface EmailAssignmentRequest {
  team: string;
  message?: string;
}

interface AgenticTask {
  id: string;
  status: string;
  team: string;
}

interface Team {
  name: string;
  description: string;
}
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private apiUrl = environment.apiUrl || 'http://localhost:8000/api';

  // ==================== Email Endpoints ====================

  /**
   * Get paginated list of emails
   */
  getEmails(limit = 50, offset = 0): Observable<EmailListResponse> {
    const params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    return this.http.get<EmailListResponse>(`${this.apiUrl}/emails`, { params });
  }

  /**
   * Get single email by ID
   */
  getEmail(id: number): Observable<Email> {
    return this.http.get<Email>(`${this.apiUrl}/emails/${id}`);
  }

  /**
   * Process email (extract CTAs, detect phishing, etc.)
   */
  processEmail(id: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/emails/${id}/process`, {});
  }

  /**
   * Enrich email with wiki keywords and employee directory
   */
  enrichEmail(id: number): Observable<any> {
    return this.http.post(`${this.apiUrl}/emails/${id}/enrich`, {});
  }

  /**
   * Assign email to a team
   */
  assignTeam(id: number, data: EmailAssignmentRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/emails/${id}/assign-team`, data);
  }

  /**
   * Mark email as read/unread
   */
  toggleRead(id: number, read: boolean): Observable<any> {
    return this.http.patch(`${this.apiUrl}/emails/${id}`, { read });
  }

  /**
   * Flag/unflag email
   */
  toggleFlag(id: number, flagged: boolean): Observable<any> {
    return this.http.patch(`${this.apiUrl}/emails/${id}`, { flagged });
  }

  /**
   * Delete email
   */
  deleteEmail(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/emails/${id}`);
  }

  // ==================== Statistics Endpoints ====================

  /**
   * Get overall statistics
   */
  getStatistics(): Observable<Statistics> {
    return this.http.get<Statistics>(`${this.apiUrl}/statistics`);
  }

  // ==================== Agentic Workflow Endpoints ====================

  /**
   * Get available teams
   */
  getTeams(): Observable<{ teams: Team[] }> {
    return this.http.get<{ teams: Team[] }>(`${this.apiUrl}/agentic/teams`);
  }

  /**
   * Get agentic task status
   */
  getAgenticTask(taskId: string): Observable<AgenticTask> {
    return this.http.get<AgenticTask>(`${this.apiUrl}/agentic/tasks/${taskId}`);
  }

  /**
   * Get all agentic tasks for a team
   */
  getAgenticTasksByTeam(team: string): Observable<AgenticTask[]> {
    const params = new HttpParams().set('team', team);
    return this.http.get<AgenticTask[]>(`${this.apiUrl}/agentic/tasks`, { params });
  }

  /**
   * Send chat message to agentic team during analysis
   */
  sendChatMessage(taskId: string, message: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/agentic/task/${taskId}/chat`, { message });
  }

  /**
   * Direct query to team (not tied to specific email)
   */
  directQuery(team: string, query: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/agentic/direct`, { team, query });
  }

  /**
   * Update team configuration
   */
  updateTeam(team: string, config: Team): Observable<any> {
    return this.http.put(`${this.apiUrl}/agentic/teams/${team}`, config);
  }

  // ==================== Model Predictions ====================

  /**
   * Get prediction from all ML models
   */
  getPredictions(emailId: number): Observable<any> {
    return this.http.get(`${this.apiUrl}/emails/${emailId}/predictions`);
  }

  // ==================== Health Check ====================

  /**
   * Check API health
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/../health`);
  }
}
