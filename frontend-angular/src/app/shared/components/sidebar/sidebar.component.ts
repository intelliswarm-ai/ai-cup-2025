import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

interface NavItem {
  label: string;
  route: string;
  icon: string;
}

interface NavSection {
  header?: string;
  items: NavItem[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss'
})
export class SidebarComponent {
  navSections: NavSection[] = [
    {
      items: [
        { label: 'Dashboard', route: '/dashboard', icon: 'dashboard' },
        { label: 'Mailbox', route: '/mailbox', icon: 'email' },
        { label: 'Daily Inbox Digest', route: '/daily-inbox-digest', icon: 'summarize' }
      ]
    },
    {
      header: 'Virtual Teams',
      items: [
        { label: 'Fraud Unit', route: '/agentic-teams', icon: 'security' },
        { label: 'Compliance', route: '/agentic-teams', icon: 'gavel' },
        { label: 'Investments', route: '/agentic-teams', icon: 'query_stats' }
      ]
    }
  ];
}
