import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { filter, map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { PageStateService } from '../../../core/services/page-state.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.scss'
})
export class NavbarComponent implements OnInit {
  title: string = 'Dashboard';
  lastUpdate$: Observable<string>;

  constructor(
    private router: Router,
    private pageState: PageStateService
  ) {
    this.lastUpdate$ = this.pageState.lastUpdate$;
  }

  ngOnInit(): void {
    // Set initial title
    this.updateTitle(this.router.url);

    // Listen to route changes
    this.router.events
      .pipe(
        filter(event => event instanceof NavigationEnd),
        map(event => (event as NavigationEnd).urlAfterRedirects)
      )
      .subscribe(url => {
        this.updateTitle(url);
      });
  }

  private updateTitle(url: string): void {
    if (url.includes('/dashboard')) {
      this.title = 'Dashboard';
    } else if (url.includes('/mailbox')) {
      this.title = 'Mailbox';
      this.pageState.clearLastUpdate(); // Clear timestamp on other pages
    } else if (url.includes('/daily-inbox-digest')) {
      this.title = 'Daily Inbox Digest';
      this.pageState.clearLastUpdate();
    } else if (url.includes('/agentic-teams')) {
      this.title = 'AI Bank Teams - Virtual Collaboration';
      this.pageState.clearLastUpdate();
    } else {
      this.title = 'Dashboard';
    }
  }
}
