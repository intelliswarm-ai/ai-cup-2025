# Angular Frontend - Email Management System

Modern Angular 18 frontend for the AI-powered email management and fraud detection system.

## 🚀 Quick Start

```bash
# Install dependencies (if not already done)
npm install

# Start development server
npm start

# Open browser
# http://localhost:4200/dashboard
```

## ✅ What's Working Now

### Dashboard Component (`/dashboard`)
Fully functional statistics dashboard displaying:
- **Total Emails**: Real-time count from backend (currently 7,101)
- **Unread**: Unprocessed emails count (7,031)
- **Phishing**: Detected phishing attempts (28)
- **Fraud Detected**: Risk-flagged cases (28)
- **Email Distribution**: Legitimate, Processed, LLM Processed counts

### Core Infrastructure
- ✅ NgRx State Management (Statistics store)
- ✅ API Service (complete REST client)
- ✅ SSE Service (real-time event streaming)
- ✅ TypeScript Models (Email, Workflow, Statistics)
- ✅ Bootstrap 5 Styling
- ✅ Material Icons
- ✅ Lazy-loaded Routes
- ✅ Redux DevTools Integration

## 📁 Project Structure

```
frontend-angular/
├── src/
│   ├── app/
│   │   ├── core/                    # Core services and models
│   │   │   ├── models/              # TypeScript interfaces
│   │   │   │   ├── email.model.ts
│   │   │   │   ├── workflow.model.ts
│   │   │   │   └── statistics.model.ts
│   │   │   └── services/            # Singleton services
│   │   │       ├── api.service.ts   # REST API client
│   │   │       └── sse.service.ts   # Server-Sent Events
│   │   │
│   │   ├── features/                # Feature modules
│   │   │   └── dashboard/           # Dashboard feature ✅
│   │   │       ├── components/
│   │   │       │   └── stats-card.component.ts
│   │   │       └── dashboard.component.ts
│   │   │
│   │   ├── store/                   # NgRx state management
│   │   │   ├── statistics/          # Statistics store ✅
│   │   │   │   ├── statistics.actions.ts
│   │   │   │   ├── statistics.reducer.ts
│   │   │   │   ├── statistics.effects.ts
│   │   │   │   └── statistics.selectors.ts
│   │   │   └── index.ts             # Root store config
│   │   │
│   │   ├── app.component.ts         # Root component
│   │   ├── app.config.ts            # App providers
│   │   └── app.routes.ts            # Route configuration
│   │
│   ├── environments/                # Environment configs
│   │   └── environment.ts           # API URLs
│   │
│   └── styles.scss                  # Global styles
│
├── test-integration.js              # Integration test script
├── TESTING.md                       # Test documentation
└── README.md                        # This file
```

## 🛠️ Available Commands

```bash
# Development
npm start              # Start dev server (http://localhost:4200)
npm run build          # Production build

# Testing
npm test               # Unit tests (Karma + Jasmine)
node test-integration.js  # Integration tests

# Code Quality
npm run lint           # Lint TypeScript files
```

## 🔌 Backend Integration

### API Endpoints Used
- `GET /api/statistics` - Dashboard statistics ✅
- `GET /api/emails` - Email list (planned)
- `GET /api/events` - SSE event stream (planned)

### Environment Configuration
Update `src/environments/environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',  // Backend API
  sseUrl: 'http://localhost:8000/api/events'  // SSE endpoint
};
```

## 📊 State Management (NgRx)

### Current Stores
- **Statistics Store** ✅ - Dashboard statistics with auto-refresh

### Store Architecture
```typescript
// Dispatch action
store.dispatch(loadStatistics());

// Select data
store.select(selectTotalEmails)  // Observable<number>
```

### Using Redux DevTools
1. Install [Redux DevTools Extension](https://github.com/reduxjs/redux-devtools)
2. Open browser DevTools
3. Click "Redux" tab
4. Inspect actions, state, and time-travel debug

## 🎨 Styling

### Bootstrap 5
All Bootstrap classes are available:
```html
<div class="container-fluid">
  <div class="row">
    <div class="col-md-6">...</div>
  </div>
</div>
```

### Material Icons
```html
<i class="material-icons">email</i>
<i class="material-icons">warning</i>
<i class="material-icons">check_circle</i>
```

### Custom Theme Colors
```scss
$primary: #e91e63;    // Pink
$secondary: #42424a;  // Dark gray
```

## 🧪 Testing

### Run Integration Tests
```bash
node test-integration.js
```

Expected output:
```
✅ Backend API responding
✅ Frontend serving Angular app
✅ Dashboard route accessible
```

### Manual Testing
1. Start backend: `docker-compose up` (from parent directory)
2. Start frontend: `npm start`
3. Open: `http://localhost:4200/dashboard`
4. Verify statistics display correctly

## 📈 Performance

### Bundle Sizes
- **Initial Bundle**: 373.04 KB
- **Dashboard Lazy Chunk**: 13.49 KB
- **First Contentful Paint**: < 500ms
- **Time to Interactive**: < 1s

### Optimization
- Lazy-loaded routes
- Ahead-of-Time (AOT) compilation
- Tree-shaking in production builds
- OnPush change detection (planned)

## 🔜 Coming Next

### Phase 3: Shared Components (Next)
- Sidebar navigation
- Header component
- Email card component
- Progress tracker component

### Phase 5: Mailbox (Upcoming)
- Email list view
- Email detail view
- Fraud detection modal
- Interactive chat interface
- Real-time SSE updates

### Phase 6: Agentic Teams (Upcoming)
- Team management
- Workflow configuration
- Discussion panel
- Email queue

## 🐛 Troubleshooting

### Dev Server Won't Start
```bash
rm -rf node_modules package-lock.json
npm install
npm start
```

### API Calls Fail (CORS Errors)
1. Ensure backend is running: `docker-compose up`
2. Check backend CORS config allows `http://localhost:4200`
3. Verify API URL in `environment.ts`

### Statistics Not Loading
1. Check browser console for errors
2. Open Redux DevTools to inspect state
3. Check Network tab - `/api/statistics` should return 200
4. Verify backend is accessible: `curl http://localhost:8000/api/statistics`

### Build Errors
```bash
rm -rf .angular
npm run build
```

## 📚 Documentation

- **Migration Guide**: `../ANGULAR_MIGRATION_GUIDE.md`
- **Migration Status**: `../ANGULAR_MIGRATION_STATUS.md`
- **Testing Guide**: `./TESTING.md`
- **Angular Docs**: https://angular.dev
- **NgRx Docs**: https://ngrx.io

## 🤝 Contributing

### Creating a New Feature Component
```bash
# Generate component
ng generate component features/your-feature --standalone

# Generate child component
ng generate component features/your-feature/components/child --standalone
```

### Adding a New Store Slice
```bash
# Create store directory
mkdir -p src/app/store/your-slice

# Create files
touch src/app/store/your-slice/your-slice.actions.ts
touch src/app/store/your-slice/your-slice.reducer.ts
touch src/app/store/your-slice/your-slice.effects.ts
touch src/app/store/your-slice/your-slice.selectors.ts
```

Then add to `store/index.ts`:
```typescript
import { yourSliceReducer } from './your-slice/your-slice.reducer';

export interface AppState {
  statistics: StatisticsState;
  yourSlice: YourSliceState;  // Add here
}

export const reducers: ActionReducerMap<AppState> = {
  statistics: statisticsReducer,
  yourSlice: yourSliceReducer  // Add here
};
```

## 📞 Support

For issues or questions:
- Check the troubleshooting section above
- Review `TESTING.md` for test guidance
- Inspect Redux DevTools for state issues
- Check browser console and Network tab
- Ensure backend is running and accessible

## ✨ Tech Stack

- **Angular**: 18.x (Standalone Components)
- **TypeScript**: 5.x
- **NgRx**: 18.x (Store, Effects, DevTools)
- **RxJS**: 7.x
- **Bootstrap**: 5.3.x
- **Material Icons**: Latest
- **Chart.js**: 4.x (planned for charts)

---

**Status**: Dashboard complete and functional ✅
**Progress**: 35.7% of migration complete
**Last Updated**: 2025-11-13
