import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-stats-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card h-100">
      <div class="card-header p-3 pt-2 position-relative">
        <div
          class="icon icon-lg icon-shape text-center border-radius-xl mt-n4 position-absolute shadow-{{shadowColor}}"
          [ngClass]="iconClass">
          <i class="material-icons-round opacity-10">{{ icon }}</i>
        </div>
        <div class="text-end pt-1">
          <p class="text-sm mb-0 text-capitalize text-secondary">{{ title }}</p>
          <h4 class="mb-0 font-weight-bolder">{{ value | number }}</h4>
        </div>
      </div>
      @if (footer) {
        <hr class="dark horizontal my-0">
        <div class="card-footer p-3">
          <p class="mb-0">
            @if (percentage !== undefined) {
              <span [ngClass]="percentageClass">
                <i class="material-icons-round text-sm">{{ percentageIcon }}</i>
                {{ percentage }}%
              </span>
            }
            <span class="text-sm text-secondary">{{ footer }}</span>
          </p>
        </div>
      }
    </div>
  `,
  styles: [`
    .card {
      background: white;
      border: 0;
      border-radius: 0.75rem;
      box-shadow: 0 20px 27px 0 rgba(0,0,0,0.05);
      position: relative;
      min-height: 1px;
      word-wrap: break-word;
    }

    .card-header {
      position: relative;
      padding: 1.5rem;
    }

    .icon {
      width: 64px;
      height: 64px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 0.75rem;
    }

    .icon-lg {
      width: 64px;
      height: 64px;
    }

    .border-radius-xl {
      border-radius: 0.75rem;
    }

    .mt-n4 {
      margin-top: -1.5rem !important;
    }

    .position-absolute {
      position: absolute !important;
    }

    .position-relative {
      position: relative !important;
    }

    .text-end {
      text-align: end !important;
    }

    .pt-1 {
      padding-top: 0.25rem !important;
    }

    .text-sm {
      font-size: 0.875rem;
      line-height: 1.5;
    }

    .text-secondary {
      color: #8392AB !important;
    }

    .mb-0 {
      margin-bottom: 0 !important;
    }

    .font-weight-bolder {
      font-weight: 700 !important;
    }

    h4 {
      font-size: 1.5rem;
      font-weight: 600;
      line-height: 1.375;
    }

    /* Material Dashboard gradients */
    .bg-gradient-dark {
      background-image: linear-gradient(195deg, #42424a 0%, #191919 100%);
    }

    .bg-gradient-primary {
      background-image: linear-gradient(195deg, #EC407A 0%, #D81B60 100%);
    }

    .bg-gradient-success {
      background-image: linear-gradient(195deg, #66BB6A 0%, #43A047 100%);
    }

    .bg-gradient-warning {
      background-image: linear-gradient(195deg, #FFA726 0%, #FB8C00 100%);
    }

    .bg-gradient-danger {
      background-image: linear-gradient(195deg, #EF5350 0%, #E53935 100%);
    }

    .bg-gradient-info {
      background-image: linear-gradient(195deg, #49A3F1 0%, #1A73E8 100%);
    }

    /* Shadows */
    .shadow-dark {
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(0, 0, 0, 0.4);
    }

    .shadow-primary {
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(233, 30, 99, 0.4);
    }

    .shadow-success {
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(76, 175, 80, 0.4);
    }

    .shadow-warning {
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(255, 152, 0, 0.4);
    }

    .shadow-danger {
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(244, 67, 54, 0.4);
    }

    .shadow-info {
      box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(0, 188, 212, 0.4);
    }

    .text-success {
      color: #66BB6A !important;
    }

    .text-danger {
      color: #EF5350 !important;
    }

    .opacity-10 {
      opacity: 1 !important;
    }

    i.material-icons-round {
      color: white;
      font-size: 24px;
    }
  `]
})
export class StatsCardComponent {
  @Input() title = '';
  @Input() value: number = 0;
  @Input() icon = 'mail';
  @Input() iconClass = 'bg-gradient-primary';
  @Input() shadowColor = 'primary';
  @Input() footer = '';
  @Input() percentage?: number;
  @Input() percentageClass = 'text-success';
  @Input() percentageIcon = 'arrow_upward';
}
