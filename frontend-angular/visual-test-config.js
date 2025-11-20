/**
 * Visual Regression Testing Configuration
 *
 * This file contains the complete mapping between vanilla JS pages and Angular routes,
 * along with element selectors for comprehensive testing.
 */

export const CONFIG = {
  // Server URLs
  VANILLA_URL: 'https://localhost',
  ANGULAR_URL: 'http://localhost:4200',
  OUTPUT_DIR: './visual-regression-results',

  // Archive previous results by date
  ARCHIVE_RESULTS: false,
  ARCHIVE_DIR: './visual-regression-history',

  // Screenshot settings
  VIEWPORT: {
    width: 1920,
    height: 1080
  },

  // Wait time for page load (ms)
  WAIT_TIME: 10000,

  // Pixelmatch threshold (0.0 = strict, 1.0 = loose)
  DIFF_THRESHOLD: 0.1,

  // Similarity threshold for passing (%)
  PASS_THRESHOLD: 95,

  // Browser options
  IGNORE_HTTPS_ERRORS: true
};

/**
 * Complete page mapping between vanilla and Angular
 *
 * status:
 * - 'implemented': Angular route exists and works
 * - 'redirect': Angular redirects to another page
 * - 'pending': Not yet implemented in Angular
 */
export const PAGES = [
  // Implemented pages
  {
    name: 'dashboard',
    vanillaPath: '/pages/dashboard.html',
    angularPath: '/dashboard',
    status: 'implemented',
    description: 'Main dashboard with statistics and charts'
  },
  {
    name: 'mailbox',
    vanillaPath: '/pages/mailbox.html',
    angularPath: '/mailbox',
    status: 'implemented',
    description: 'Email inbox and management'
  },

  // Agentic Teams - Virtual AI Teams
  {
    name: 'agentic-teams',
    vanillaPath: '/pages/agentic-teams.html',
    angularPath: '/agentic-teams',
    status: 'implemented',
    description: 'AI agent teams configuration'
  },
  {
    name: 'daily-inbox-digest',
    vanillaPath: '/pages/daily-inbox-digest.html',
    angularPath: '/daily-inbox-digest',
    status: 'implemented',
    description: 'Daily email digest summary'
  },

  // Pending pages (not yet implemented in Angular)
  {
    name: 'billing',
    vanillaPath: '/pages/billing.html',
    angularPath: '/billing',
    status: 'pending',
    description: 'Billing and subscription management'
  },
  {
    name: 'profile',
    vanillaPath: '/pages/profile.html',
    angularPath: '/profile',
    status: 'pending',
    description: 'User profile and settings'
  },
  {
    name: 'notifications',
    vanillaPath: '/pages/notifications.html',
    angularPath: '/notifications',
    status: 'pending',
    description: 'Notification center'
  },
  {
    name: 'tables',
    vanillaPath: '/pages/tables.html',
    angularPath: '/tables',
    status: 'pending',
    description: 'Data tables and reports'
  },
  {
    name: 'icons',
    vanillaPath: '/pages/icons.html',
    angularPath: '/icons',
    status: 'pending',
    description: 'Icon library reference'
  },
  {
    name: 'typography',
    vanillaPath: '/pages/typography.html',
    angularPath: '/typography',
    status: 'pending',
    description: 'Typography styles reference'
  },
  {
    name: 'sign-in',
    vanillaPath: '/pages/sign-in.html',
    angularPath: '/sign-in',
    status: 'pending',
    description: 'Login page'
  },
  {
    name: 'sign-up',
    vanillaPath: '/pages/sign-up.html',
    angularPath: '/sign-up',
    status: 'pending',
    description: 'Registration page'
  },
  {
    name: 'virtual-reality',
    vanillaPath: '/pages/virtual-reality.html',
    angularPath: '/virtual-reality',
    status: 'pending',
    description: 'VR interface (future feature)'
  },
  {
    name: 'rtl',
    vanillaPath: '/pages/rtl.html',
    angularPath: '/rtl',
    status: 'pending',
    description: 'Right-to-left language support demo'
  },
  {
    name: 'map',
    vanillaPath: '/pages/map.html',
    angularPath: '/map',
    status: 'pending',
    description: 'Geographic map view'
  }
];

/**
 * Common elements present on all/most pages
 */
export const COMMON_ELEMENTS = [
  { name: 'Sidebar', selector: '#sidenav-main' },
  { name: 'Navbar', selector: '.navbar-main' },
  { name: 'Main Content', selector: 'main.main-content' },
  { name: 'Footer', selector: 'footer' }
];

/**
 * Page-specific elements to inspect
 */
export const ELEMENTS_TO_INSPECT = {
  dashboard: [
    ...COMMON_ELEMENTS,
    { name: 'Total Emails Card', selector: '.col-xl-3:nth-child(1) .card' },
    { name: 'Processed Card', selector: '.col-xl-3:nth-child(2) .card' },
    { name: 'Legitimate Card', selector: '.col-xl-3:nth-child(3) .card' },
    { name: 'Phishing Card', selector: '.col-xl-3:nth-child(4) .card' },
    { name: 'Distribution Chart', selector: 'canvas:first-of-type' },
    { name: 'Workflow Chart', selector: 'canvas:nth-of-type(2)' },
    { name: 'Virtual Teams Header', selector: '.nav-item.mt-3 h6' }
  ],

  mailbox: [
    ...COMMON_ELEMENTS,
    { name: 'Statistics Cards', selector: '.row:first-child' },
    { name: 'Quick Actions', selector: '.card:has(.card-header)' },
    { name: 'Email List', selector: '.email-card:first-child' },
    { name: 'Filter Buttons', selector: '.btn-group' },
    { name: 'Search Input', selector: 'input[type="text"]' }
  ],

  'agentic-teams': [
    ...COMMON_ELEMENTS,
    { name: 'Team Cards', selector: '.card.team-card' },
    { name: 'Agent List', selector: '.agent-list' },
    { name: 'Configuration Panel', selector: '.config-panel' }
  ],

  'daily-inbox-digest': [
    ...COMMON_ELEMENTS,
    { name: 'Digest Summary', selector: '.digest-summary' },
    { name: 'Email Categories', selector: '.category-section' },
    { name: 'Action Buttons', selector: '.action-buttons' }
  ],

  billing: [
    ...COMMON_ELEMENTS,
    { name: 'Billing Cards', selector: '.card' },
    { name: 'Payment Methods', selector: '.payment-method' },
    { name: 'Invoice Table', selector: 'table' },
    { name: 'Subscription Info', selector: '.subscription-info' }
  ],

  profile: [
    ...COMMON_ELEMENTS,
    { name: 'Profile Header', selector: '.profile-header' },
    { name: 'Avatar', selector: '.avatar' },
    { name: 'Form Fields', selector: 'form .form-group' },
    { name: 'Save Button', selector: 'button[type="submit"]' }
  ],

  notifications: [
    ...COMMON_ELEMENTS,
    { name: 'Notification List', selector: '.notification-item' },
    { name: 'Filter Tabs', selector: '.nav-tabs' },
    { name: 'Mark Read Button', selector: '.mark-read-btn' }
  ],

  tables: [
    ...COMMON_ELEMENTS,
    { name: 'Data Table', selector: 'table' },
    { name: 'Table Header', selector: 'thead' },
    { name: 'Table Rows', selector: 'tbody tr' },
    { name: 'Pagination', selector: '.pagination' }
  ],

  icons: [
    ...COMMON_ELEMENTS,
    { name: 'Icon Grid', selector: '.icon-grid' },
    { name: 'Icon Examples', selector: '.icon-example' }
  ],

  typography: [
    ...COMMON_ELEMENTS,
    { name: 'Heading Examples', selector: 'h1, h2, h3, h4, h5, h6' },
    { name: 'Paragraph Examples', selector: 'p' },
    { name: 'Text Variants', selector: '.text-examples' }
  ],

  'sign-in': [
    { name: 'Login Form', selector: 'form' },
    { name: 'Email Input', selector: 'input[type="email"]' },
    { name: 'Password Input', selector: 'input[type="password"]' },
    { name: 'Sign In Button', selector: 'button[type="submit"]' },
    { name: 'Logo', selector: '.logo' }
  ],

  'sign-up': [
    { name: 'Registration Form', selector: 'form' },
    { name: 'Form Fields', selector: '.form-group' },
    { name: 'Sign Up Button', selector: 'button[type="submit"]' },
    { name: 'Terms Checkbox', selector: 'input[type="checkbox"]' }
  ],

  'virtual-reality': [
    ...COMMON_ELEMENTS,
    { name: 'VR Container', selector: '.vr-container' },
    { name: 'VR Controls', selector: '.vr-controls' }
  ],

  rtl: [
    ...COMMON_ELEMENTS,
    { name: 'RTL Content', selector: '[dir="rtl"]' }
  ],

  map: [
    ...COMMON_ELEMENTS,
    { name: 'Map Container', selector: '#map' },
    { name: 'Map Controls', selector: '.map-controls' }
  ]
};

/**
 * CSS properties to compare for each element
 */
export const STYLE_PROPERTIES = [
  'backgroundColor',
  'color',
  'fontSize',
  'fontWeight',
  'fontFamily',
  'padding',
  'margin',
  'borderRadius',
  'boxShadow',
  'display',
  'position',
  'width',
  'height',
  'opacity',
  'border',
  'textAlign'
];
