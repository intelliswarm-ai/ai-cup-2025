import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Email, TeamAssignment } from '../models/email.model';

@Injectable({
  providedIn: 'root'
})
export class EmailService {
  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/emails`;

  getEmails(limit: number = 50, offset: number = 0): Observable<Email[]> {
    const params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());
    return this.http.get<Email[]>(this.apiUrl, { params });
  }

  getEmailById(id: number): Observable<Email> {
    return this.http.get<Email>(`${this.apiUrl}/${id}`);
  }

  fetchEmailsFromMailpit(): Observable<{ fetched: number; total_in_mailpit: number }> {
    return this.http.post<{ fetched: number; total_in_mailpit: number }>(`${this.apiUrl}/fetch`, {});
  }

  processAllEmails(): Observable<{ count: number }> {
    return this.http.post<{ count: number }>(`${this.apiUrl}/process-all`, {});
  }

  assignTeamToEmail(assignment: TeamAssignment): Observable<Email> {
    return this.http.post<Email>(
      `${this.apiUrl}/${assignment.emailId}/assign-team`,
      { team: assignment.team, message: assignment.message }
    );
  }

  startFraudDetection(emailId: number, message?: string): Observable<{ status: string; session_id: string }> {
    return this.http.post<{ status: string; session_id: string }>(
      `${this.apiUrl}/${emailId}/fraud-detect`,
      { message }
    );
  }
}
