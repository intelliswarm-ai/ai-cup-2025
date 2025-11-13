import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component')
      .then(m => m.DashboardComponent)
  },
  {
    path: 'mailbox',
    loadComponent: () => import('./features/mailbox/mailbox.component')
      .then(m => m.MailboxComponent)
  },
  {
    path: 'daily-inbox-digest',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'agentic-teams',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  }
  // Future routes (to be added during migration):
  // Will be replaced with actual components once migrated
];
