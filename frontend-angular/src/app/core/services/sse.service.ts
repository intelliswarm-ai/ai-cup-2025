import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { ProgressUpdate } from '../models';
import { environment } from '../../../environments/environment';

export interface SSEEvent {
  type: string;
  data: any;
}

@Injectable({
  providedIn: 'root'
})
export class SseService {
  private eventSource: EventSource | null = null;
  private events$ = new Subject<SSEEvent>();
  private isConnected = false;

  /**
   * Connect to SSE endpoint
   */
  connect(): Observable<SSEEvent> {
    if (!this.isConnected) {
      const url = environment.sseUrl || 'http://localhost:8000/api/events';

      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log('[SSE] Connected');
        this.isConnected = true;
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.events$.next({ type: data.type || 'message', data });
        } catch (error) {
          console.error('[SSE] Failed to parse message:', error);
        }
      };

      this.eventSource.onerror = (error) => {
        console.error('[SSE] Error:', error);
        this.isConnected = false;
        // Attempt reconnection after 5 seconds
        setTimeout(() => {
          if (!this.isConnected) {
            console.log('[SSE] Attempting to reconnect...');
            this.disconnect();
            this.connect();
          }
        }, 5000);
      };

      // Register specific event listeners
      this.registerEventListeners();
    }

    return this.events$.asObservable();
  }

  /**
   * Register listeners for specific SSE event types
   */
  private registerEventListeners(): void {
    if (!this.eventSource) return;

    const eventTypes = [
      'emails_fetched',
      'email_processed',
      'email_enriched',
      'agentic_message',
      'agentic_progress',
      'agentic_complete',
      'agentic_error',
      'agentic_chat_response',
      'agentic_chat_user',
      'statistics_updated'
    ];

    eventTypes.forEach(type => {
      this.eventSource!.addEventListener(type, (event: any) => {
        try {
          const data = JSON.parse(event.data);
          this.events$.next({ type, data });
        } catch (error) {
          console.error(`[SSE] Failed to parse ${type} event:`, error);
        }
      });
    });
  }

  /**
   * Filter events by type
   */
  onEvent(eventType: string): Observable<any> {
    return new Observable(observer => {
      const subscription = this.events$.subscribe(event => {
        if (event.type === eventType) {
          observer.next(event.data);
        }
      });

      return () => subscription.unsubscribe();
    });
  }

  /**
   * Filter events by task ID (for agentic workflows)
   */
  onTaskEvent(taskId: string): Observable<ProgressUpdate> {
    return new Observable(observer => {
      const subscription = this.events$.subscribe(event => {
        if (event.data.task_id === taskId) {
          observer.next(event.data as ProgressUpdate);
        }
      });

      return () => subscription.unsubscribe();
    });
  }

  /**
   * Disconnect from SSE
   */
  disconnect(): void {
    if (this.eventSource) {
      console.log('[SSE] Disconnecting');
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
    }
  }

  /**
   * Check if SSE is connected
   */
  get connected(): boolean {
    return this.isConnected;
  }
}
