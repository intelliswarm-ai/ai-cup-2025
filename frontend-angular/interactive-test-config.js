/**
 * Interactive Button-Click Testing Configuration
 *
 * This configuration defines button interactions for each page
 * to enable comprehensive visual regression testing of button actions
 */

export const INTERACTIVE_CONFIG = {
  // Test settings
  WAIT_AFTER_CLICK: 2000, // Wait time after clicking a button (ms)
  WAIT_BEFORE_SCREENSHOT: 500, // Wait before taking screenshot (ms)
  MAX_DEPTH: 3, // Maximum click depth to avoid infinite loops

  // Scroll settings
  ENABLE_SCROLLING: true, // Enable scrolling tests
  SCROLL_STEPS: 5, // Number of scroll steps (top -> middle -> bottom)
  SCROLL_WAIT: 1000, // Wait time between scrolls (ms)
  SCROLL_AMOUNT: 500, // Pixels to scroll per step

  // Modal and page detection
  DETECT_MODALS: true, // Automatically detect and test modals
  DETECT_NEW_PAGES: true, // Test pages that open from clicks
  MODAL_SELECTORS: [
    '.modal.show',
    '.modal.fade.show',
    '[role="dialog"][style*="display: block"]',
    '.offcanvas.show',
    '.drawer.open'
  ],

  // Recursive testing
  RECURSIVE_TESTING: true, // Test buttons inside modals
  TEST_MODAL_BUTTONS: true, // Click buttons inside opened modals

  // Screenshot naming pattern: {page}-{button-name}-{timestamp}
  OUTPUT_DIR: './interactive-test-results'
};

/**
 * Button interaction definitions per page
 * Each interaction includes:
 * - selector: CSS selector for the button
 * - name: Descriptive name for the screenshot
 * - action: Optional custom action (default: click)
 * - waitFor: Optional selector to wait for after click
 * - closeModal: Optional selector to close modal after test
 */
export const PAGE_INTERACTIONS = {
  dashboard: [
    {
      selector: '.btn-primary',
      name: 'primary-action',
      description: 'Test primary action button'
    }
    // Dashboard has minimal interactions - mainly display
  ],

  mailbox: [
    {
      selector: 'button:has-text("Fetch Emails from MailPit")',
      name: 'fetch-emails',
      description: 'Fetch emails from MailPit',
      waitFor: '.email-card'
    },
    {
      selector: 'button:has-text("Process All Unprocessed")',
      name: 'process-all',
      description: 'Process all unprocessed emails',
      waitFor: '.spinner-border'
    },
    {
      selector: 'button:has-text("Refresh")',
      name: 'refresh',
      description: 'Refresh email list'
    },
    {
      selector: '.email-card:first-child',
      name: 'open-first-email',
      description: 'Open first email details',
      waitFor: '.modal.show',
      closeModal: '.modal .btn-close'
    }
  ],

  billing: [
    {
      selector: '.btn-primary',
      name: 'upgrade-plan',
      description: 'Test upgrade plan button'
    },
    {
      selector: '.btn-outline-primary',
      name: 'view-invoice',
      description: 'Test view invoice button'
    }
  ],

  profile: [
    {
      selector: 'button[type="submit"]',
      name: 'save-profile',
      description: 'Save profile changes'
    },
    {
      selector: '.avatar-upload',
      name: 'change-avatar',
      description: 'Test avatar upload'
    }
  ],

  notifications: [
    {
      selector: '.mark-read-btn',
      name: 'mark-all-read',
      description: 'Mark all notifications as read'
    },
    {
      selector: '.notification-item:first-child',
      name: 'open-first-notification',
      description: 'Open first notification'
    },
    {
      selector: '.filter-tabs .nav-link:nth-child(2)',
      name: 'filter-unread',
      description: 'Filter unread notifications'
    }
  ],

  tables: [
    {
      selector: '.pagination .page-item:last-child',
      name: 'next-page',
      description: 'Navigate to next page'
    },
    {
      selector: 'thead th:first-child',
      name: 'sort-first-column',
      description: 'Sort by first column'
    },
    {
      selector: 'tbody tr:first-child .btn',
      name: 'row-action',
      description: 'Test row action button'
    }
  ],

  icons: [
    {
      selector: '.icon-example:first-child',
      name: 'copy-icon',
      description: 'Copy icon code'
    }
  ],

  typography: [
    // Typography is mostly static display
  ],

  'sign-in': [
    {
      selector: 'button[type="submit"]',
      name: 'submit-login',
      description: 'Submit login form'
    },
    {
      selector: 'a[href*="forgot"]',
      name: 'forgot-password',
      description: 'Click forgot password link'
    }
  ],

  'sign-up': [
    {
      selector: 'button[type="submit"]',
      name: 'submit-registration',
      description: 'Submit registration form'
    },
    {
      selector: 'input[type="checkbox"]',
      name: 'toggle-terms',
      description: 'Toggle terms acceptance'
    }
  ],

  'virtual-reality': [
    {
      selector: '.vr-controls button',
      name: 'vr-action',
      description: 'Test VR control'
    }
  ],

  rtl: [
    // RTL is mainly layout test
  ],

  map: [
    {
      selector: '.map-controls .zoom-in',
      name: 'zoom-in',
      description: 'Zoom in on map'
    },
    {
      selector: '.map-controls .zoom-out',
      name: 'zoom-out',
      description: 'Zoom out on map'
    }
  ]
};

/**
 * Form interactions for testing input fields
 * These test filling forms before clicking submit
 */
export const FORM_INTERACTIONS = {
  'sign-in': {
    fields: [
      { selector: 'input[type="email"]', value: 'test@example.com' },
      { selector: 'input[type="password"]', value: 'testpassword123' }
    ]
  },

  'sign-up': {
    fields: [
      { selector: 'input[name="name"]', value: 'Test User' },
      { selector: 'input[type="email"]', value: 'test@example.com' },
      { selector: 'input[type="password"]', value: 'testpassword123' },
      { selector: 'input[type="checkbox"]', action: 'check' }
    ]
  },

  profile: {
    fields: [
      { selector: 'input[name="firstName"]', value: 'John' },
      { selector: 'input[name="lastName"]', value: 'Doe' },
      { selector: 'input[name="email"]', value: 'john.doe@example.com' }
    ]
  }
};
