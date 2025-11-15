import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

import { StatsCardComponent } from './components/stats-card.component';
import { Statistics } from '../../core/models';
import {
  selectStatistics,
  selectStatisticsLoading,
  selectTotalEmails,
  selectUnreadCount,
  selectPhishingCount,
  selectFraudDetected
} from '../../store';
import { loadStatistics } from '../../store/statistics/statistics.actions';
import * as EmailsActions from '../../store/emails/emails.actions';
import { PageStateService } from '../../core/services/page-state.service';
import { SseService } from '../../core/services/sse.service';
import { EmailService } from '../../core/services/email.service';

// Register Chart.js components
Chart.register(...registerables);

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, StatsCardComponent],
  template: `
    <div class="container-fluid py-4">
      <!-- Loading State -->
      @if (loading$ | async) {
        <div class="row">
          <div class="col-12 text-center py-5">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Loading statistics...</p>
          </div>
        </div>
      }

      <!-- Statistics Cards -->
      <div class="row">
        <!-- Total Emails -->
        <div class="col-xl-3 col-sm-6 mb-xl-0 mb-4">
          <app-stats-card
            title="Total Emails"
            [value]="(totalEmails$ | async) || 0"
            icon="mail"
            iconClass="bg-gradient-dark"
            shadowColor="dark"
          />
        </div>

        <!-- Processed -->
        <div class="col-xl-3 col-sm-6 mb-xl-0 mb-4">
          @if (statistics$ | async; as stats) {
            <app-stats-card
              title="Processed"
              [value]="stats.processed_emails || 0"
              icon="done_all"
              iconClass="bg-gradient-primary"
              shadowColor="primary"
            />
          }
        </div>

        <!-- Legitimate -->
        <div class="col-xl-3 col-sm-6 mb-xl-0 mb-4">
          @if (statistics$ | async; as stats) {
            <app-stats-card
              title="Legitimate"
              [value]="stats.legitimate_emails || 0"
              icon="check_circle"
              iconClass="bg-gradient-success"
              shadowColor="success"
            />
          }
        </div>

        <!-- Phishing Detected -->
        <div class="col-xl-3 col-sm-6">
          <app-stats-card
            title="Phishing Detected"
            [value]="(phishingCount$ | async) || 0"
            icon="warning"
            iconClass="bg-gradient-danger"
            shadowColor="danger"
          />
        </div>
      </div>

      <!-- Charts Row -->
      @if (statistics$ | async; as stats) {
        <div class="row mt-4">
          <div class="col-lg-6 col-md-6 mb-md-0 mb-4">
            <div class="card">
              <div class="card-header pb-0">
                <div class="row">
                  <div class="col-lg-6 col-7">
                    <h6>Email Distribution</h6>
                    <p class="text-sm mb-0">
                      <i class="fa fa-check text-info" aria-hidden="true"></i>
                      <span class="font-weight-bold ms-1">{{ getDetectionRate(stats) }}%</span> detection rate
                    </p>
                  </div>
                </div>
              </div>
              <div class="card-body p-3">
                <canvas #distributionChart height="300"></canvas>
              </div>
            </div>
          </div>
          <div class="col-lg-6 col-md-6">
            <div class="card">
              <div class="card-header pb-0">
                <h6 class="mb-0">Workflow Detection Results</h6>
              </div>
              <div class="card-body p-3">
                <canvas #workflowChart height="300"></canvas>
              </div>
            </div>
          </div>
        </div>

        <!-- Processing Status & Quick Actions -->
        <div class="row mt-4">
          <div class="col-lg-8 col-md-6 mb-md-0 mb-4">
            <div class="card">
              <div class="card-header pb-0">
                <h6>Processing Status</h6>
              </div>
              <div class="card-body px-0 pb-2">
                <div class="px-4">
                  <div class="progress-wrapper">
                    <div class="progress-info">
                      <div class="progress-percentage">
                        <span class="text-sm font-weight-bold">{{ getProcessingPercentage(stats) }}% processed</span>
                      </div>
                    </div>
                    <div class="progress">
                      <div class="progress-bar bg-gradient-primary" role="progressbar"
                           [attr.aria-valuenow]="getProcessingPercentage(stats)"
                           aria-valuemin="0"
                           aria-valuemax="100"
                           [style.width.%]="getProcessingPercentage(stats)"></div>
                    </div>
                  </div>
                  <div class="mt-4">
                    <p class="text-sm mb-2"><strong>Ready to start?</strong></p>
                    <ol class="text-sm">
                      <li>Check MailPit has emails: <a href="http://localhost:8025" target="_blank">http://localhost:8025</a></li>
                      <li>Fetch emails from MailPit to database</li>
                      <li>Run phishing detection workflows</li>
                      <li>View results in the Mailbox</li>
                    </ol>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-lg-4 col-md-6">
            <div class="card h-100">
              <div class="card-header pb-0">
                <h6>Quick Actions</h6>
              </div>
              <div class="card-body p-3">
                <div class="d-flex flex-column gap-3">
                  <button
                    [class]="fetcherRunning ? 'btn btn-danger w-100' : 'btn btn-primary w-100'"
                    (click)="toggleFetcher()"
                    [disabled]="fetcherToggling">
                    <i class="material-icons-round">{{ fetcherRunning ? 'stop' : 'download' }}</i>
                    <span>{{ fetcherRunning ? 'Stop Fetcher' : 'Start Fetcher' }}</span>
                  </button>
                  @if (fetcherRunning) {
                    <div class="text-sm text-center" style="padding: 8px; background: #e3f2fd; border-radius: 4px;">
                      <strong>Fetching:</strong> <span>{{ fetchProgress }}</span>
                    </div>
                  }
                  <button class="btn btn-success w-100" (click)="processAll()">
                    <i class="material-icons-round">play_arrow</i> Process All
                  </button>
                  <button class="btn btn-info w-100" (click)="refresh()">
                    <i class="material-icons-round">refresh</i> Refresh
                  </button>
                  <a routerLink="/mailbox" class="btn btn-outline-primary w-100">
                    <i class="material-icons-round">email</i> View Mailbox
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .icon {
      width: 48px;
      height: 48px;
      border-radius: 0.75rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .icon i {
      color: white;
      font-size: 24px;
    }

    .bg-gradient-success {
      background: linear-gradient(195deg, #66BB6A 0%, #43A047 100%);
    }

    .bg-gradient-warning {
      background: linear-gradient(195deg, #FFA726 0%, #FB8C00 100%);
    }

    .bg-gradient-info {
      background: linear-gradient(195deg, #49A3F1 0%, #1A73E8 100%);
    }

    .card {
      background: white;
      border-radius: 0.75rem;
      box-shadow: 0 20px 27px 0 rgba(0,0,0,0.05);
    }
  `]
})
export class DashboardComponent implements OnInit, OnDestroy, AfterViewInit {
  private store = inject(Store);
  private pageState = inject(PageStateService);
  private sseService = inject(SseService);
  private emailService = inject(EmailService);

  @ViewChild('distributionChart') distributionChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('workflowChart') workflowChartRef!: ElementRef<HTMLCanvasElement>;

  private distributionChart?: Chart;
  private workflowChart?: Chart;
  private destroy$ = new Subject<void>();

  // Observable streams from store
  statistics$: Observable<Statistics | null>;
  loading$: Observable<boolean>;
  totalEmails$: Observable<number>;
  unreadCount$: Observable<number>;
  phishingCount$: Observable<number>;
  fraudDetected$: Observable<number>;

  // Fetcher status
  fetcherRunning = false;
  fetchProgress = 'Batch 0, 0 emails';
  fetcherToggling = false;

  constructor() {
    this.statistics$ = this.store.select(selectStatistics);
    this.loading$ = this.store.select(selectStatisticsLoading);
    this.totalEmails$ = this.store.select(selectTotalEmails);
    this.unreadCount$ = this.store.select(selectUnreadCount);
    this.phishingCount$ = this.store.select(selectPhishingCount);
    this.fraudDetected$ = this.store.select(selectFraudDetected);
  }

  ngOnInit(): void {
    // Dispatch action to load statistics
    this.store.dispatch(loadStatistics());

    // Connect to SSE for real-time updates
    this.connectSSE();

    // Load workflow statistics once on initial page load
    this.loadWorkflowStats();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.sseService.disconnect();
  }

  ngAfterViewInit(): void {
    this.initCharts();

    // Update charts when statistics change
    this.statistics$.subscribe(stats => {
      if (stats) {
        this.updateCharts(stats);
        // Update last refresh timestamp
        const now = new Date();
        const timeStr = now.toLocaleTimeString();
        this.pageState.setLastUpdate(`(Updated: ${timeStr})`);
      }
    });
  }

  private connectSSE(): void {
    console.log('[Dashboard] Connecting to SSE...');
    this.sseService.connect().pipe(
      takeUntil(this.destroy$)
    ).subscribe();

    // Handle fetch_started event
    this.sseService.onEvent('fetch_started').pipe(
      takeUntil(this.destroy$)
    ).subscribe(() => {
      console.log('[Dashboard SSE] Fetch started');
      this.fetcherRunning = true;
    });

    // Handle emails_fetched event (batch progress)
    this.sseService.onEvent('emails_fetched').pipe(
      takeUntil(this.destroy$)
    ).subscribe((data: any) => {
      console.log(`[Dashboard SSE] Batch ${data.batch}: ${data.fetched_in_batch} emails (Total: ${data.total_fetched})`);
      this.fetchProgress = `Batch ${data.batch}, ${data.total_fetched} emails fetched`;
      // Reload statistics to get updated counts
      this.store.dispatch(loadStatistics());
    });

    // Handle fetch_completed event
    this.sseService.onEvent('fetch_completed').pipe(
      takeUntil(this.destroy$)
    ).subscribe((data: any) => {
      console.log(`[Dashboard SSE] Fetch completed: ${data.total_fetched} total emails in ${data.batches} batches`);
      this.fetcherRunning = false;
      this.fetchProgress = 'Batch 0, 0 emails';
      // Reload statistics
      this.store.dispatch(loadStatistics());
    });

    // Handle fetch_stopped event
    this.sseService.onEvent('fetch_stopped').pipe(
      takeUntil(this.destroy$)
    ).subscribe(() => {
      console.log('[Dashboard SSE] Fetch stopped');
      this.fetcherRunning = false;
      this.fetchProgress = 'Batch 0, 0 emails';
    });

    // Handle fetch_error event
    this.sseService.onEvent('fetch_error').pipe(
      takeUntil(this.destroy$)
    ).subscribe((data: any) => {
      console.error('[Dashboard SSE] Fetch error:', data.message);
      this.fetcherRunning = false;
      this.fetchProgress = 'Batch 0, 0 emails';
    });

    // Handle statistics_updated event
    this.sseService.onEvent('statistics_updated').pipe(
      takeUntil(this.destroy$)
    ).subscribe(() => {
      console.log('[Dashboard SSE] Statistics updated');
      this.store.dispatch(loadStatistics());
    });
  }

  toggleFetcher(): void {
    if (this.fetcherToggling) {
      return;
    }

    this.fetcherToggling = true;

    if (this.fetcherRunning) {
      // Stop fetcher
      console.log('[Dashboard] Stopping email fetcher...');
      this.emailService.stopFetcher().subscribe({
        next: (result) => {
          console.log('[Dashboard] Fetcher stopped:', result);
          this.fetcherToggling = false;
        },
        error: (error) => {
          console.error('[Dashboard] Error stopping fetcher:', error);
          this.fetcherToggling = false;
        }
      });
    } else {
      // Start fetcher
      console.log('[Dashboard] Starting email fetcher...');
      this.emailService.startFetcher().subscribe({
        next: (result) => {
          console.log('[Dashboard] Fetcher started:', result);
          this.fetcherToggling = false;
        },
        error: (error) => {
          console.error('[Dashboard] Error starting fetcher:', error);
          this.fetcherToggling = false;
        }
      });
    }
  }

  private loadWorkflowStats(): void {
    console.log('[Dashboard] Loading workflow stats for 100 most recent emails...');

    this.emailService.getRecentEmailsForWorkflowStats().subscribe({
      next: (emails) => {
        console.log(`[Dashboard] Processing ${emails.length} emails for workflow stats`);

        // Count detections by workflow
        const workflowStats = {
          'URL Analysis': { phishing: 0, safe: 0 },
          'Sender Analysis': { phishing: 0, safe: 0 },
          'Content Analysis': { phishing: 0, safe: 0 }
        };

        // Process emails
        emails.forEach(email => {
          if (email.workflow_results && email.workflow_results.length > 0) {
            email.workflow_results.forEach(result => {
              const workflow = result.workflow_name;
              if (workflowStats[workflow as keyof typeof workflowStats]) {
                if (result.is_phishing_detected) {
                  workflowStats[workflow as keyof typeof workflowStats].phishing++;
                } else {
                  workflowStats[workflow as keyof typeof workflowStats].safe++;
                }
              }
            });
          }
        });

        console.log('[Dashboard] Workflow stats:', workflowStats);

        // Update workflow chart
        if (this.workflowChart) {
          this.workflowChart.data.datasets[0].data = [
            workflowStats['URL Analysis'].phishing,
            workflowStats['Sender Analysis'].phishing,
            workflowStats['Content Analysis'].phishing
          ];
          this.workflowChart.data.datasets[1].data = [
            workflowStats['URL Analysis'].safe,
            workflowStats['Sender Analysis'].safe,
            workflowStats['Content Analysis'].safe
          ];
          this.workflowChart.update();
        }
      },
      error: (error) => {
        console.error('[Dashboard] Error loading workflow stats:', error);
      }
    });
  }

  private initCharts(): void {
    // Email Distribution Doughnut Chart
    const distributionConfig: ChartConfiguration<'doughnut'> = {
      type: 'doughnut',
      data: {
        labels: ['Legitimate', 'Phishing', 'Pending'],
        datasets: [{
          data: [0, 0, 0],
          backgroundColor: [
            'rgba(107, 142, 111, 0.85)',   // Mild Sage Green
            'rgba(139, 21, 56, 0.85)',     // Burgundy
            'rgba(184, 85, 27, 0.85)'      // Bronze/Orange
          ],
          borderColor: [
            'rgba(107, 142, 111, 1)',
            'rgba(139, 21, 56, 1)',
            'rgba(184, 85, 27, 1)'
          ],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              font: {
                family: 'Roboto',
                size: 12
              },
              color: '#5B5550'
            }
          }
        }
      }
    };

    // Workflow Results Bar Chart
    const workflowConfig: ChartConfiguration<'bar'> = {
      type: 'bar',
      data: {
        labels: ['URL Analysis', 'Sender Analysis', 'Content Analysis'],
        datasets: [{
          label: 'Phishing Detected',
          data: [0, 0, 0],
          backgroundColor: 'rgba(139, 21, 56, 0.85)',    // Burgundy
          borderColor: 'rgba(139, 21, 56, 1)',
          borderWidth: 2
        }, {
          label: 'Safe',
          data: [0, 0, 0],
          backgroundColor: 'rgba(107, 142, 111, 0.85)',  // Mild Sage Green
          borderColor: 'rgba(107, 142, 111, 1)',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              font: {
                family: 'Roboto',
                size: 12
              },
              color: '#5B5550'
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              color: '#5B5550',
              font: {
                family: 'Roboto',
                size: 11
              }
            },
            grid: {
              color: 'rgba(213, 211, 207, 0.3)'
            }
          },
          x: {
            ticks: {
              color: '#5B5550',
              font: {
                family: 'Roboto',
                size: 11
              }
            },
            grid: {
              display: false
            }
          }
        }
      }
    };

    this.distributionChart = new Chart(this.distributionChartRef.nativeElement, distributionConfig);
    this.workflowChart = new Chart(this.workflowChartRef.nativeElement, workflowConfig);
  }

  private updateCharts(stats: Statistics): void {
    // Update distribution chart
    if (this.distributionChart) {
      const legitimate = stats.legitimate_emails || 0;
      const phishing = stats.phishing_detected || 0;
      const pending = stats.unprocessed_emails || 0;

      this.distributionChart.data.datasets[0].data = [legitimate, phishing, pending];
      this.distributionChart.update();
    }
    // Note: workflow chart is updated separately by loadWorkflowStats()
  }

  getDetectionRate(stats: Statistics): number {
    if (!stats || !stats.processed_emails || stats.processed_emails === 0) return 0;
    const phishing = stats.phishing_detected || 0;
    return Math.round((phishing / stats.processed_emails) * 100 * 10) / 10;
  }

  getProcessingPercentage(stats: Statistics): number {
    if (!stats || !stats.total_emails || stats.total_emails === 0) return 0;
    const processed = stats.processed_emails || 0;
    return Math.round((processed / stats.total_emails) * 100);
  }

  processAll(): void {
    this.store.dispatch(EmailsActions.processAllEmails());
  }

  refresh(): void {
    this.store.dispatch(loadStatistics());
  }
}
