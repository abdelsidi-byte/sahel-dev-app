# Sahel Dev - Technical Specification

## 1. Concept & Vision

**Sahel Dev** هو SaaS عربي متخصص في API Monitoring و Status Pages.
المشروع يستهدف السوق العربي والفرنسي والأفريقي.

**Slogan**: "رصد بلا حدود" (Monitoring Without Limits)

## 2. Design Language

### Colors
- Primary: #60A5FA (Blue)
- Secondary: #A78BFA (Purple)
- Accent: #F472B6 (Pink)
- Background: #0F172A (Dark)
- Surface: #1E293B (Card bg)
- Text: #F8FAFC (White)
- Muted: #94A3B8 (Gray)

### Typography
- Headings: Inter, sans-serif
- Body: Segoe UI, sans-serif
- Arabic: Noto Sans Arabic

### Motion
- Hover: scale(1.02), 200ms ease
- Page transitions: fade, 300ms
- Loading: pulse animation

## 3. Features

### MVP Features (Phase 1)
1. User signup/login (Google, GitHub, Email)
2. Create API endpoint for monitoring
3. Set check interval (1min, 5min, 15min)
4. Create status page (custom subdomain)
5. Add alert channels (Slack, Discord, Email)
6. View uptime history (30 days)

### Future Features
- Custom branding for status pages
- Incident management
- Team collaboration
- API for integrations

## 4. Technical Architecture

### Frontend (Next.js 14)
```
/app
├── page.tsx           # Landing page
├── dashboard/         # User dashboard
├── status/[slug]/    # Public status pages
└── api/               # API routes
```

### Backend (FastAPI)
```
/api
├── auth/              # Authentication
├── monitors/          # API monitoring CRUD
├── status-pages/      # Status page management
├── alerts/            # Alert channels
└── checks/            # Health check execution
```

### Database Schema

**users**
- id (UUID)
- email (string)
- name (string)
- plan (enum: free, pro, enterprise)
- created_at

**monitors**
- id (UUID)
- user_id (FK)
- name (string)
- url (string)
- method (enum: GET, POST)
- interval (int: seconds)
- created_at

**status_pages**
- id (UUID)
- user_id (FK)
- slug (string, unique)
- title (string)
- created_at

**incidents**
- id (UUID)
- monitor_id (FK)
- status (enum: detected, resolved)
- started_at
- resolved_at

## 5. API Endpoints

### Auth
- POST /api/auth/signup
- POST /api/auth/login
- GET /api/auth/me

### Monitors
- GET /api/monitors
- POST /api/monitors
- GET /api/monitors/{id}
- PUT /api/monitors/{id}
- DELETE /api/monitors/{id}

### Status Pages
- GET /api/status-pages
- POST /api/status-pages
- GET /api/status/{slug}

### Checks
- GET /api/checks/{monitor_id}

## 6. Pricing Logic

```python
def get_plan_limits(plan):
    limits = {
        'free': {'monitors': 1, 'status_pages': 1, 'interval': 300},
        'pro': {'monitors': -1, 'status_pages': -1, 'interval': 60},
        'enterprise': {'monitors': -1, 'status_pages': -1, 'interval': 30}
    }
    return limits[plan]
```

## 7. Deployment

### Infrastructure
- **Frontend**: Vercel (auto-deploy from main)
- **Backend**: Railway (FastAPI)
- **Database**: Neon PostgreSQL
- **Monitoring Workers**: Separate Railway service

### Environment Variables
```
DATABASE_URL=postgresql://...
JWT_SECRET=your-secret-key
SLACK_WEBHOOK_URL=...
DISCORD_WEBHOOK_URL=...
```
