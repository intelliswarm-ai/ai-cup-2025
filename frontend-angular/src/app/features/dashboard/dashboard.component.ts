import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { takeUntil, debounceTime, filter } from 'rxjs/operators';
import { Chart, ChartConfiguration, registerables } from 'chart.js';
import { HttpClient } from '@angular/common/http';

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

// Configure smoother animations globally
Chart.defaults.animation = {
  duration: 400,
  easing: 'easeInOutQuart'
};

interface EnrichedStats {
  email_analysis: any;
  workflow_execution: any;
  team_assignments: any;
  tools_usage: any;
  time_saved: any;
}

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

      <!-- Time Saved Highlight (Hero Section) -->
      @if (enrichedStats) {
        <div class="row mt-4">
          <div class="col-12">
            <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
              <div class="card-body p-4">
                <div class="row align-items-center">
                  <div class="col-lg-3 text-center">
                    <i class="material-icons-round" style="font-size: 72px; opacity: 0.9;">schedule</i>
                  </div>
                  <div class="col-lg-9">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                      <h3 class="text-white mb-0">Total Time Saved</h3>
                      <p class="text-white-50 mb-0" style="font-size: 0.875rem;">
                        <i class="material-icons-round" style="font-size: 1rem; vertical-align: middle;">info</i>
                        View breakdown in "Time Saved Breakdown" chart below
                      </p>
                    </div>
                    <div class="row">
                      <div class="col-md-4">
                        <h2 class="text-white fw-bold mb-0">{{ enrichedStats.time_saved.total_hours }} hrs</h2>
                        <p class="text-white-50 mb-0">Total Hours Saved</p>
                      </div>
                      <div class="col-md-4">
                        <h2 class="text-white fw-bold mb-0">{{ enrichedStats.time_saved.total_days }} days</h2>
                        <p class="text-white-50 mb-0">Work Days Saved</p>
                      </div>
                      <div class="col-md-4">
                        <h2 class="text-white fw-bold mb-0">{{ enrichedStats.time_saved.total_minutes }} min</h2>
                        <p class="text-white-50 mb-0">Total Minutes</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- Charts Row 1: Email Distribution & Workflow Detection -->
      <div class="row mt-4">
        <div class="col-lg-6 col-md-6 mb-4">
          <div class="card h-100">
            <div class="card-header pb-0">
              <h6>Email Distribution</h6>
              @if (statistics$ | async; as stats) {
                <p class="text-sm mb-0">
                  <i class="fa fa-check text-info" aria-hidden="true"></i>
                  <span class="font-weight-bold ms-1">{{ getDetectionRate(stats) }}%</span> detection rate
                </p>
              }
            </div>
            <div class="card-body p-3">
              <canvas #distributionChart height="320"></canvas>
            </div>
          </div>
        </div>
        <div class="col-lg-6 col-md-6 mb-4">
          <div class="card h-100">
            <div class="card-header pb-0">
              <h6>Workflow Detection Results</h6>
              <p class="text-sm mb-0">
                @if (enrichedStats) {
                  <i class="fa fa-cogs text-primary" aria-hidden="true"></i>
                  <span class="font-weight-bold ms-1">{{ enrichedStats.workflow_execution.total_workflow_executions }}</span> total executions
                }
              </p>
            </div>
            <div class="card-body p-3">
              <canvas #workflowChart height="320"></canvas>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row 2: Time Saved Breakdown & Email Categories -->
      @if (enrichedStats) {
        <div class="row mt-4">
          <div class="col-lg-8 col-md-6 mb-md-0 mb-4">
            <div class="card">
              <div class="card-header pb-0">
                <h6>Time Saved Breakdown</h6>
                <p class="text-sm mb-0">
                  <i class="fa fa-arrow-up text-success" aria-hidden="true"></i>
                  <span class="font-weight-bold ms-1">Minutes saved</span> by automation category
                </p>
              </div>
              <div class="card-body p-3">
                <canvas #timeSavedChart height="300"></canvas>
              </div>
            </div>
          </div>
          <div class="col-lg-4 col-md-6">
            <div class="card">
              <div class="card-header pb-0">
                <h6>Email Categories</h6>
                <p class="text-sm mb-0">Smart categorization distribution</p>
              </div>
              <div class="card-body p-3">
                <canvas #badgeChart height="300"></canvas>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- Charts Row 3: Team Assignments & Tools Status -->
      @if (enrichedStats) {
        <div class="row mt-4">
          <div class="col-lg-7 col-md-6 mb-md-0 mb-4">
            <div class="card">
              <div class="card-header pb-0">
                <h6>Agentic Team Assignments</h6>
                <p class="text-sm mb-0">
                  <i class="fa fa-users text-primary" aria-hidden="true"></i>
                  <span class="font-weight-bold ms-1">{{ enrichedStats.team_assignments.total_assigned }}</span> emails assigned to specialized teams
                </p>
              </div>
              <div class="card-body p-3">
                <canvas #teamAssignmentsChart height="280"></canvas>
              </div>
            </div>
          </div>
          <div class="col-lg-5 col-md-6">
            <div class="card">
              <div class="card-header pb-0">
                <h6>Tools Status</h6>
                <p class="text-sm mb-0">
                  <i class="fa fa-tools text-info" aria-hidden="true"></i>
                  <span class="font-weight-bold ms-1">{{ enrichedStats.tools_usage.total_tools }}</span> total tools in registry
                </p>
              </div>
              <div class="card-body p-3">
                <canvas #toolsChart height="280"></canvas>
              </div>
            </div>
          </div>
        </div>

        <!-- Platform Highlights Row -->
        <div class="row mt-4">
          <div class="col-lg-3 col-md-6 mb-4">
            <div class="card text-center">
              <div class="card-body p-3">
                <div class="icon bg-gradient-info mx-auto mb-3">
                  <i class="material-icons-round">summarize</i>
                </div>
                <h5 class="fw-bold">{{ enrichedStats.email_analysis.emails_with_summaries }}</h5>
                <p class="text-sm mb-0">AI Summaries Generated</p>
              </div>
            </div>
          </div>
          <div class="col-lg-3 col-md-6 mb-4">
            <div class="card text-center">
              <div class="card-body p-3">
                <div class="icon bg-gradient-success mx-auto mb-3">
                  <i class="material-icons-round">reply</i>
                </div>
                <h5 class="fw-bold">{{ enrichedStats.email_analysis.emails_with_replies }}</h5>
                <p class="text-sm mb-0">Quick Reply Drafts</p>
              </div>
            </div>
          </div>
          <div class="col-lg-3 col-md-6 mb-4">
            <div class="card text-center">
              <div class="card-body p-3">
                <div class="icon bg-gradient-warning mx-auto mb-3">
                  <i class="material-icons-round">psychology</i>
                </div>
                <h5 class="fw-bold">{{ enrichedStats.workflow_execution.total_workflow_executions }}</h5>
                <p class="text-sm mb-0">Workflow Executions</p>
              </div>
            </div>
          </div>
          <div class="col-lg-3 col-md-6 mb-4">
            <div class="card text-center">
              <div class="card-body p-3">
                <div class="icon bg-gradient-dark mx-auto mb-3">
                  <i class="material-icons-round">auto_awesome</i>
                </div>
                <h5 class="fw-bold">{{ enrichedStats.email_analysis.enriched_emails }}</h5>
                <p class="text-sm mb-0">Wiki Enriched Emails</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions Row (Compact) -->
        <div class="row mt-2">
          <div class="col-12">
            <div class="card">
              <div class="card-body p-3">
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                  <button
                    [class]="fetcherRunning ? 'btn btn-danger' : 'btn btn-primary'"
                    (click)="toggleFetcher()"
                    [disabled]="fetcherToggling">
                    <i class="material-icons-round">{{ fetcherRunning ? 'stop' : 'download' }}</i>
                    <span>{{ fetcherRunning ? 'Stop Fetcher' : 'Start Fetcher' }}</span>
                  </button>
                  @if (fetcherRunning) {
                    <span class="badge bg-info d-flex align-items-center px-3">
                      <strong>Fetching:</strong>&nbsp;{{ fetchProgress }}
                    </span>
                  }
                  <button class="btn btn-success" (click)="processAll()">
                    <i class="material-icons-round">play_arrow</i> Process All
                  </button>
                  <button class="btn btn-info" (click)="refresh()">
                    <i class="material-icons-round">refresh</i> Refresh
                  </button>
                  <a routerLink="/mailbox" class="btn btn-outline-primary">
                    <i class="material-icons-round">email</i> View Mailbox
                  </a>
                  <a routerLink="/agentic-teams" class="btn btn-outline-secondary">
                    <i class="material-icons-round">groups</i> Agentic Teams
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
  private http = inject(HttpClient);

  @ViewChild('distributionChart') distributionChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('workflowChart') workflowChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('timeSavedChart') timeSavedChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('badgeChart') badgeChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('teamAssignmentsChart') teamAssignmentsChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('toolsChart') toolsChartRef!: ElementRef<HTMLCanvasElement>;

  private distributionChart?: Chart;
  private workflowChart?: Chart;
  private timeSavedChart?: Chart;
  private badgeChart?: Chart;
  private teamAssignmentsChart?: Chart;
  private toolsChart?: Chart;
  private destroy$ = new Subject<void>();

  // Observable streams from store
  statistics$: Observable<Statistics | null>;
  loading$: Observable<boolean>;
  totalEmails$: Observable<number>;
  unreadCount$: Observable<number>;
  phishingCount$: Observable<number>;
  fraudDetected$: Observable<number>;

  // Enriched statistics
  enrichedStats: EnrichedStats | null = null;
  enrichedLoading = false;
  private enrichedChartsUpdating = false;

  // Time saved calculation details for tooltips
  private timeSavedCalculations: any = {};

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

    // Load enriched statistics (includes workflow stats)
    this.loadEnrichedStats();

    // Connect to SSE for real-time updates
    this.connectSSE();
  }

  private loadEnrichedStats(): void {
    this.enrichedLoading = true;
    this.http.get<EnrichedStats>('http://localhost:8000/api/dashboard/enriched-stats')
      .subscribe({
        next: (stats) => {
          this.enrichedStats = stats;
          this.enrichedLoading = false;

          // Update charts (wait for chart initialization if needed)
          setTimeout(() => {
            if (this.workflowChart) {
              this.updateEnrichedCharts(stats);
            }
          }, 300);
        },
        error: (error) => {
          console.error('[Dashboard] Error loading enriched stats:', error);
          this.enrichedLoading = false;
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.sseService.disconnect();
  }

  ngAfterViewInit(): void {
    this.initCharts();

    // Update charts when statistics change (with debouncing to prevent trembling)
    this.statistics$.pipe(
      filter(stats => stats !== null), // Filter out null values
      debounceTime(150), // Debounce rapid updates
      takeUntil(this.destroy$)
    ).subscribe(stats => {
      this.updateCharts(stats);
      // Update last refresh timestamp
      const now = new Date();
      const timeStr = now.toLocaleTimeString();
      this.pageState.setLastUpdate(`(Updated: ${timeStr})`);
    });

    // If enriched stats are already loaded, update charts
    if (this.enrichedStats) {
      setTimeout(() => {
        this.updateEnrichedCharts(this.enrichedStats!);
      }, 200);
    }
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
      this.loadEnrichedStats(); // Reload enriched stats too
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
    // Check if chart elements are available
    if (!this.distributionChartRef || !this.workflowChartRef) {
      return;
    }

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

    // Workflow Results Bar Chart (Stacked)
    const workflowConfig: ChartConfiguration<'bar'> = {
      type: 'bar',
      data: {
        labels: ['URL Analysis', 'Sender Analysis', 'Content Analysis'],
        datasets: [{
          label: 'Detected: Phishing',
          data: [0, 0, 0],
          backgroundColor: 'rgba(139, 21, 56, 0.85)',    // Burgundy
          borderColor: 'rgba(139, 21, 56, 1)',
          borderWidth: 2,
          stack: 'detected'
        }, {
          label: 'Detected: Legitimate',
          data: [0, 0, 0],
          backgroundColor: 'rgba(107, 142, 111, 0.85)',  // Mild Sage Green
          borderColor: 'rgba(107, 142, 111, 1)',
          borderWidth: 2,
          stack: 'detected'
        }
        // REMOVED: Ground Truth datasets
        // Ground truth labels are training data and should not be shown to users
      ]
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
            stacked: true,
            beginAtZero: true,
            ticks: {
              stepSize: 10,
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
            stacked: true,
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
    // Initialize charts if they don't exist yet
    if (!this.distributionChart && this.distributionChartRef) {
      this.initCharts();
    }

    // Update distribution chart
    if (this.distributionChart) {
      const legitimate = stats.legitimate_emails || 0;
      const phishing = stats.phishing_detected || 0;
      const pending = stats.unprocessed_emails || 0;

      this.distributionChart.data.datasets[0].data = [legitimate, phishing, pending];
      this.distributionChart.update();
    }
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
    this.loadEnrichedStats();
  }

  private updateEnrichedCharts(stats: EnrichedStats): void {
    // Prevent simultaneous updates
    if (this.enrichedChartsUpdating) return;
    this.enrichedChartsUpdating = true;

    // Update Workflow Chart from enriched stats
    if (this.workflowChart && stats.workflow_execution && stats.workflow_execution.workflows) {
      const workflows = stats.workflow_execution.workflows;

      // Filter to main workflows (not agentic ones)
      const mainWorkflows = workflows.filter((w: any) =>
        w.workflow_name.startsWith('ML:') ||
        w.workflow_name.includes('Analysis')
      ).slice(0, 5); // Limit to top 5 workflows

      if (mainWorkflows.length > 0) {
        this.workflowChart.data.labels = mainWorkflows.map((w: any) =>
          w.workflow_name.replace('ML: ', '').replace(' Analysis', '')
        );

        // Detected results
        this.workflowChart.data.datasets[0].data = mainWorkflows.map((w: any) => w.phishing_detected || 0);
        this.workflowChart.data.datasets[1].data = mainWorkflows.map((w: any) => w.safe_detected || 0);

        // REMOVED: Ground truth data population
        // Ground truth labels are training data and should not be shown to users

        this.workflowChart.update();
      }
    }

    // Update Time Saved Chart (Bar chart)
    if (this.timeSavedChartRef && !this.timeSavedChart) {
      this.initTimeSavedChart();
    }
    if (this.timeSavedChart && stats.time_saved) {
      const breakdown = stats.time_saved.breakdown;
      const calculations = stats.time_saved.calculations;

      // Update chart data
      this.timeSavedChart.data.datasets[0].data = [
        breakdown.email_review || 0,
        breakdown.phishing_detection || 0,
        breakdown.summary_generation || 0,
        breakdown.reply_drafting || 0,
        breakdown.team_routing || 0,
        breakdown.wiki_enrichment || 0,
        breakdown.daily_digest || 0
      ];

      // Store calculation details for tooltips
      if (calculations) {
        this.timeSavedCalculations = [
          calculations.email_review,
          calculations.phishing_detection,
          calculations.summary_generation,
          calculations.reply_drafting,
          calculations.team_routing,
          calculations.wiki_enrichment,
          calculations.daily_digest
        ];
      }

      this.timeSavedChart.update();
    }

    // Update Badge Chart (Doughnut chart)
    if (this.badgeChartRef && !this.badgeChart) {
      this.initBadgeChart();
    }
    if (this.badgeChart && stats.email_analysis && stats.email_analysis.badge_breakdown) {
      const badges = stats.email_analysis.badge_breakdown;
      this.badgeChart.data.datasets[0].data = Object.values(badges);
      this.badgeChart.update();
    }

    // Update Team Assignments Chart (Bar chart)
    if (this.teamAssignmentsChartRef && !this.teamAssignmentsChart) {
      this.initTeamAssignmentsChart();
    }
    if (this.teamAssignmentsChart && stats.team_assignments) {
      const assignments = stats.team_assignments.assignments_by_team || {};
      this.teamAssignmentsChart.data.labels = Object.keys(assignments);
      this.teamAssignmentsChart.data.datasets[0].data = Object.values(assignments);
      this.teamAssignmentsChart.update();
    }

    // Update Tools Chart (Doughnut chart)
    if (this.toolsChartRef && !this.toolsChart) {
      this.initToolsChart();
    }
    if (this.toolsChart && stats.tools_usage) {
      this.toolsChart.data.datasets[0].data = [
        stats.tools_usage.available_tools || 0,
        stats.tools_usage.unavailable_tools || 0
      ];
      this.toolsChart.update();
    }

    // Reset flag after a brief delay to allow new updates
    setTimeout(() => {
      this.enrichedChartsUpdating = false;
    }, 200);
  }

  private initTimeSavedChart(): void {
    if (!this.timeSavedChartRef) return;

    const config: ChartConfiguration<'bar'> = {
      type: 'bar',
      data: {
        labels: ['Email Review', 'Phishing Detection', 'Summary Gen', 'Reply Drafting', 'Team Routing', 'Wiki Enrich', 'Daily Digest'],
        datasets: [{
          label: 'Minutes Saved',
          data: [0, 0, 0, 0, 0, 0, 0],
          backgroundColor: [
            'rgba(103, 126, 175, 0.85)',
            'rgba(139, 21, 56, 0.85)',
            'rgba(107, 142, 111, 0.85)',
            'rgba(184, 85, 27, 0.85)',
            'rgba(146, 111, 165, 0.85)',
            'rgba(200, 150, 90, 0.85)',
            'rgba(220, 180, 100, 0.85)'  // Gold for Daily Digest
          ],
          borderColor: [
            'rgba(103, 126, 175, 1)',
            'rgba(139, 21, 56, 1)',
            'rgba(107, 142, 111, 1)',
            'rgba(184, 85, 27, 1)',
            'rgba(146, 111, 165, 1)',
            'rgba(200, 150, 90, 1)',
            'rgba(220, 180, 100, 1)'
          ],
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleFont: {
              size: 14,
              weight: 'bold'
            },
            bodyFont: {
              size: 13
            },
            callbacks: {
              title: (context: any) => {
                return context[0].label;
              },
              label: (context: any) => {
                const value = context.parsed.y;
                return `Time Saved: ${value.toFixed(1)} minutes`;
              },
              afterLabel: (context: any) => {
                const calc = this.timeSavedCalculations[context.dataIndex];
                if (calc) {
                  return [
                    '',
                    `Calculation:`,
                    `${calc.count} ${calc.unit} × ${calc.rate} min`,
                    `= ${(calc.count * calc.rate).toFixed(1)} minutes`
                  ];
                }
                return '';
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              color: '#5B5550',
              font: {
                family: 'Roboto',
                size: 11
              }
            }
          },
          x: {
            ticks: {
              color: '#5B5550',
              font: {
                family: 'Roboto',
                size: 10
              }
            }
          }
        }
      }
    };

    this.timeSavedChart = new Chart(this.timeSavedChartRef.nativeElement, config);
  }

  private initBadgeChart(): void {
    if (!this.badgeChartRef) return;

    const config: ChartConfiguration<'doughnut'> = {
      type: 'doughnut',
      data: {
        labels: ['Meeting', 'Risk', 'External', 'Automated', 'VIP', 'Follow Up', 'Newsletter', 'Finance'],
        datasets: [{
          data: [0, 0, 0, 0, 0, 0, 0, 0],
          backgroundColor: [
            'rgba(103, 126, 175, 0.85)',
            'rgba(139, 21, 56, 0.85)',
            'rgba(184, 85, 27, 0.85)',
            'rgba(107, 142, 111, 0.85)',
            'rgba(200, 150, 90, 0.85)',
            'rgba(146, 111, 165, 0.85)',
            'rgba(150, 180, 200, 0.85)',
            'rgba(180, 130, 150, 0.85)'
          ],
          borderColor: [
            'rgba(103, 126, 175, 1)',
            'rgba(139, 21, 56, 1)',
            'rgba(184, 85, 27, 1)',
            'rgba(107, 142, 111, 1)',
            'rgba(200, 150, 90, 1)',
            'rgba(146, 111, 165, 1)',
            'rgba(150, 180, 200, 1)',
            'rgba(180, 130, 150, 1)'
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
                size: 11
              },
              color: '#5B5550'
            }
          }
        }
      }
    };

    this.badgeChart = new Chart(this.badgeChartRef.nativeElement, config);
  }

  private initTeamAssignmentsChart(): void {
    if (!this.teamAssignmentsChartRef) return;

    const config: ChartConfiguration<'bar'> = {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Emails Assigned',
          data: [],
          backgroundColor: 'rgba(107, 142, 111, 0.85)',
          borderColor: 'rgba(107, 142, 111, 1)',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              color: '#5B5550',
              font: {
                family: 'Roboto',
                size: 11
              }
            }
          },
          y: {
            ticks: {
              color: '#5B5550',
              font: {
                family: 'Roboto',
                size: 11
              }
            }
          }
        }
      }
    };

    this.teamAssignmentsChart = new Chart(this.teamAssignmentsChartRef.nativeElement, config);
  }

  private initToolsChart(): void {
    if (!this.toolsChartRef) return;

    const config: ChartConfiguration<'doughnut'> = {
      type: 'doughnut',
      data: {
        labels: ['Available Tools', 'Needs Configuration'],
        datasets: [{
          data: [0, 0],
          backgroundColor: [
            'rgba(107, 142, 111, 0.85)',
            'rgba(184, 85, 27, 0.85)'
          ],
          borderColor: [
            'rgba(107, 142, 111, 1)',
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

    this.toolsChart = new Chart(this.toolsChartRef.nativeElement, config);
  }
}
