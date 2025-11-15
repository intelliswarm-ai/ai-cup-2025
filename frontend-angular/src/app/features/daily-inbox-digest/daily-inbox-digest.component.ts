import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

type BadgeType = 'MEETING' | 'RISK' | 'EXTERNAL' | 'AUTOMATED' | 'VIP' | 'FOLLOW_UP' | 'NEWSLETTER' | 'FINANCE';

interface EmailSummary {
  id: number;
  subject: string;
  sender: string;
  recipient?: string;
  received_at: string;
  summary: string[];
  body_text?: string;
  has_cta: boolean;
  cta_text?: string;
  cta_type?: string;
  badges: BadgeType[];
  processed?: boolean;
  is_phishing?: boolean;
}

interface GroupedEmails {
  [category: string]: EmailSummary[];
}

interface DigestStats {
  total_today: number;
  badge_counts: { [key in BadgeType]?: number };
}

interface CallToAction {
  email_id: number;
  subject: string;
  cta_text: string;
  cta_type: string;
  category: BadgeType;
}

@Component({
  selector: 'app-daily-inbox-digest',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './daily-inbox-digest.component.html',
  styleUrl: './daily-inbox-digest.component.scss'
})
export class DailyInboxDigestComponent implements OnInit {
  groupedEmails: GroupedEmails = {};
  availableCategories: BadgeType[] = [];
  selectedCategories: Set<BadgeType> = new Set();

  stats: DigestStats = {
    total_today: 0,
    badge_counts: {}
  };

  allCallToActions: CallToAction[] = [];

  selectedEmail: EmailSummary | null = null;
  showEmailModal: boolean = false;

  badgeIcons: { [key in BadgeType]: string } = {
    'MEETING': 'event',
    'RISK': 'shield',
    'EXTERNAL': 'close',
    'AUTOMATED': 'settings',
    'VIP': 'star',
    'FOLLOW_UP': 'cached',
    'NEWSLETTER': 'email',
    'FINANCE': 'attach_money'
  };

  badgeClasses: { [key in BadgeType]: string } = {
    'MEETING': 'badge-meeting',
    'RISK': 'badge-risk',
    'EXTERNAL': 'badge-external',
    'AUTOMATED': 'badge-automated',
    'VIP': 'badge-vip',
    'FOLLOW_UP': 'badge-follow-up',
    'NEWSLETTER': 'badge-newsletter',
    'FINANCE': 'badge-finance'
  };

  ngOnInit(): void {
    this.loadMockData();
  }

  loadMockData(): void {
    // Mock email data
    this.groupedEmails = {
      'MEETING': [
        {
          id: 1,
          subject: 'Q4 Strategy Planning - All Hands',
          sender: 'exec-team@company.com',
          recipient: 'you@company.com',
          received_at: new Date().toISOString(),
          summary: [
            'Quarterly strategy review scheduled for next week',
            'All department heads expected to attend'
          ],
          body_text: `Dear Team,

I hope this message finds you well. I am writing to inform you about our upcoming Q4 Strategy Planning session.

Date: Next Monday, 10 AM
Location: Conference Room A

Best regards,
Executive Team`,
          has_cta: true,
          cta_text: 'Accept meeting invite',
          cta_type: 'meeting',
          badges: ['MEETING', 'VIP'],
          processed: true,
          is_phishing: false
        }
      ],
      'RISK': [
        {
          id: 2,
          subject: 'Security Alert: Unusual Login Activity',
          sender: 'security@company.com',
          received_at: new Date(Date.now() - 7200000).toISOString(),
          summary: [
            'Multiple failed login attempts detected',
            'IP address flagged from suspicious location'
          ],
          has_cta: true,
          cta_text: 'Review and verify account',
          cta_type: 'urgent',
          badges: ['RISK']
        }
      ],
      'EXTERNAL': [
        {
          id: 3,
          subject: 'Partnership Proposal - Tech Collaboration',
          sender: 'partnerships@techcorp.com',
          received_at: new Date(Date.now() - 10800000).toISOString(),
          summary: [
            'Interested in exploring partnership opportunities',
            'Focus on AI integration'
          ],
          has_cta: true,
          cta_text: 'Schedule discovery call',
          cta_type: 'external',
          badges: ['EXTERNAL', 'FOLLOW_UP']
        }
      ]
    };

    // Calculate stats
    let totalToday = 0;
    const badgeCounts: { [key in BadgeType]?: number } = {};

    Object.values(this.groupedEmails).forEach(emails => {
      totalToday += emails.length;
      emails.forEach(email => {
        email.badges.forEach(badge => {
          badgeCounts[badge] = (badgeCounts[badge] || 0) + 1;
        });
      });
    });

    this.stats = { total_today: totalToday, badge_counts: badgeCounts };

    // Get available categories
    this.availableCategories = Object.keys(this.groupedEmails).filter(
      cat => this.groupedEmails[cat].length > 0
    ) as BadgeType[];

    // Select all by default
    this.selectedCategories = new Set(this.availableCategories);

    // Extract all CTAs
    this.extractCallToActions();
  }

  extractCallToActions(): void {
    this.allCallToActions = [];
    Object.entries(this.groupedEmails).forEach(([category, emails]) => {
      emails.forEach(email => {
        if (email.has_cta && email.cta_text) {
          this.allCallToActions.push({
            email_id: email.id,
            subject: email.subject,
            cta_text: email.cta_text,
            cta_type: email.cta_type || 'action',
            category: category as BadgeType
          });
        }
      });
    });
  }

  selectAllCategories(): void {
    this.selectedCategories = new Set(this.availableCategories);
  }

  deselectAllCategories(): void {
    this.selectedCategories.clear();
  }

  toggleCategory(category: BadgeType): void {
    if (this.selectedCategories.has(category)) {
      this.selectedCategories.delete(category);
    } else {
      this.selectedCategories.add(category);
    }
  }

  isCategorySelected(category: BadgeType): boolean {
    return this.selectedCategories.has(category);
  }

  getFilteredCategories(): BadgeType[] {
    return this.availableCategories.filter(cat => this.selectedCategories.has(cat));
  }

  getEmailsForCategory(category: BadgeType): EmailSummary[] {
    return this.groupedEmails[category] || [];
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffMins < 1440) {
      return `${Math.floor(diffMins / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  viewEmail(email: EmailSummary): void {
    this.selectedEmail = email;
    this.showEmailModal = true;
  }

  closeModal(): void {
    this.showEmailModal = false;
    this.selectedEmail = null;
  }

  handleCTA(cta: CallToAction, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    console.log('CTA clicked:', cta);

    // Find the email associated with this CTA
    const email = Object.values(this.groupedEmails)
      .flat()
      .find(e => e.id === cta.email_id);

    if (email) {
      // Show the email details modal
      this.viewEmail(email);
    } else {
      // Show alert for demo
      alert(`Action: ${cta.cta_text}\nEmail: ${cta.subject}`);
    }
  }
}
