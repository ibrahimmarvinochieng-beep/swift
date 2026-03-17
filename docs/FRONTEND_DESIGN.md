# Swift Event Intelligence — Frontend Design Proposal

A comprehensive UX/UI design for the Swift Event Intelligence Platform, aligned with the **Swift — Stay Ahead.** brand identity.

---

## 1. Brand Identity

**Tagline:** *"Stay Ahead."*

- **Logo:** Stylized bird (swift) in flight with energetic orange streak — conveys speed, agility, foresight
- **Promise:** Proactive intelligence that helps users act before events unfold
- **Personality:** Professional, innovative, trustworthy, forward-thinking

**Differentiator:** This is not a generic news aggregator. It's an **event intelligence command center** that keeps you ahead — think Bloomberg Terminal meets incident response, with the clarity and energy of the Swift brand.

### Brand Assets (from concept board)

| Asset | Spec |
|-------|------|
| **Logo** | White bird + orange streak + "Swift" (white) + "Stay Ahead." (orange) |
| **Bird icon** | Solid dark blue, solid white, or white + orange streak |
| **App icons** | Rounded square/circle; Sky Gradient or Dark Slate bg; bird icon |
| **Notification** | Dark Slate bubble, bird icon, "Breaking News", "Stay Ahead with Swift." |
| **Hero** | Sky Gradient + city skyline + full logo |

---

## 2. Color & Feel

### Brand Palette (from concept board)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Electric Blue** | Primary | `#007AFF` | Primary actions, links, trust, energy |
| **Vibrant Orange** | Accent | `#FF9500` | CTAs, highlights, severity 3–4 (UI-safe variant) |
| **Bird Streak** | Logo accent | `#FFF500` | Bird icon streak, hero accents (bright) |
| **Sky Gradient** | Background (light) | `#5EDFFF` → `#00BFFF` | Hero sections, marketing, openness |
| **Dark Slate** | App background | `#0A1628` | App canvas, notification bubbles |
| **Surface** | Cards/panels | `#142338` | Cards, modals, dropdowns |
| **Border** | Dividers | `#1E3A5F` | Inputs, separators |
| **Text Primary** | Body | `#FFFFFF` | Primary text on dark |
| **Text Secondary** | Labels | `#8BA3C7` | Metadata, labels |
| **Success** | Confirmed | `#34C759` | Ingested, confirmed |
| **Warning** | Pending | `#FF9500` | Review, elevated |
| **Critical** | Errors | `#FF3B30` | Severity 5, DLQ, errors |

### Severity Scale (Visual)

| Severity | Label | Color | Badge |
|----------|-------|-------|-------|
| 1 | Low | `#8BA3C7` | Muted blue pill |
| 2 | Moderate | `#5AC8FA` | Light blue pill |
| 3 | Elevated | `#FF9500` | Orange pill (brand accent) |
| 4 | High | `#FF6B35` | Deep orange pill |
| 5 | Critical | `#FF3B30` | Red pill, subtle pulse |

### Typography

- **Headlines & CTAs:** `Montserrat Bold` — clean, modern, confident (per brand board)
- **Body:** `Montserrat` (Regular/Medium) — consistent, legible
- **Data/Numbers:** Tabular figures, Montserrat for IDs

### Feel

- **Energetic yet professional** — blue conveys trust; orange adds dynamism
- **Dark app, light marketing** — app uses Dark Slate; website uses Sky Gradient + light
- **Fluid gradients** — Sky Gradient suggests smooth UX, forward movement
- **Bird motif** — logo and app icon reinforce speed and foresight

---

## 3. Website vs Application

### Marketing Website (Public)

| Aspect | Design |
|--------|--------|
| **Purpose** | Convert visitors → sign up / book demo |
| **Tone** | Professional, innovative, "Stay Ahead" |
| **Hero** | Sky Gradient (blue → orange) over blurred city skyline; full "Swift Stay Ahead." logo in white |
| **Layout** | Hero, features, use cases, pricing, CTA |
| **Colors** | Electric Blue + Vibrant Orange on Sky Gradient / light backgrounds |
| **Navigation** | Product, Pricing, Docs, Login, Sign Up |
| **Forms** | Email capture, demo request — Montserrat Bold labels, Electric Blue focus states |

### Application (Authenticated)

| Aspect | Design |
|--------|--------|
| **Purpose** | Work: triage, ingest, analyze, act — *Stay Ahead* |
| **Tone** | Dense, efficient, professional |
| **Layout** | Sidebar + main content, Dark Slate canvas |
| **Colors** | Dark Slate background, Electric Blue accents, Orange for alerts |
| **Logo** | Bird icon (white + orange streak) in header; "Swift" + "Stay Ahead." |
| **Navigation** | Role-based: Events, Ingest, Pipeline, Admin |
| **Forms** | Ingest, filters — Electric Blue primary buttons |

### App Icons (per brand board)

- **Primary:** Rounded square, Sky Gradient background, white bird with orange streak
- **Dark mode:** Dark Slate rounded square, white bird with orange streak
- **Light/website:** White rounded square, dark blue bird
- **Favicon:** Simplified bird icon for browser tab

### Separation Strategy

- **URL:** `swiftintel.com` (website) vs `app.swiftintel.com` (app)
- **Auth gate:** Website = public; App = login required
- **Visual break:** Website = Sky Gradient, aspirational; App = Dark Slate, focused
- **Shared:** Bird logo, Montserrat, Electric Blue + Orange palette

---

## 4. Pages & Navigation

### App Structure

```
┌─────────────────────────────────────────────────────────────┐
│  [Bird] Swift                    [Search...]  [🔔] [User ▼] │
│         Stay Ahead.                                          │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│  Events  │  Main content area (Dark Slate canvas)             │
│  Ingest  │  (context-dependent)                             │
│  Pipeline│                                                  │
│  ─────── │                                                  │
│  Admin   │                                                  │
│  (admin) │                                                  │
│          │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

*Header: Bird icon (white + orange streak) left; "Swift" in Montserrat Bold; "Stay Ahead." in orange below or inline.*

### Page Inventory

| Page | Route | Role | Purpose |
|------|-------|------|---------|
| **Event Feed** | `/events` | All | Main triage view — list/grid of events |
| **Event Detail** | `/events/:id` | All | Full event, sources, entities, map |
| **Ingest** | `/ingest` | Analyst+ | Single/batch signal submission |
| **Pipeline** | `/pipeline` | All | Status, stats, manual trigger (admin) |
| **Alerts** | `/alerts` | All | Notification preferences, channels |
| **Admin** | `/admin` | Admin | Users, DLQ, keys, settings |
| **Settings** | `/settings` | All | Profile, theme, notifications |

### Navigation Rules

- **Primary nav:** 4–5 items max; collapse "Admin" for non-admins
- **Breadcrumbs:** For deep routes (e.g. Event Detail)
- **Quick actions:** FAB or command palette (`Cmd+K`) for power users
- **Contextual:** Event card → "View" / "Share" / "Add to alert"

---

## 5. Notifications Design

### In-App Notifications (Branded)

**Placement:** Top-right, stacked, max 3 visible

**Anatomy (per brand board):**
```
┌─────────────────────────────────────────────────────────────┐
│ [Bird]  Breaking News                              now      │
│         Market volatility ahead.                         [×]  │
│         Stay Ahead with Swift.                               │
└─────────────────────────────────────────────────────────────┘
```

- **Background:** Dark Slate (`#0A1628`), rounded corners
- **Icon:** Miniature white bird with orange streak (top-left)
- **Title:** "Breaking News" / "New Event" — Montserrat Bold, white
- **Body:** Event summary — concise, actionable
- **Tagline:** "Stay Ahead with Swift." — orange, smaller
- **Timestamp:** Top-right ("now", "2 min ago")
- **Close:** [×] top-right

**Types:**

| Type | Title | Color accent | Example body |
|------|-------|--------------|--------------|
| **Event** | Breaking News | Orange | "Earthquake in Chile. Severity 4." |
| **Success** | Done | Green | "Signal ingested successfully." |
| **Warning** | Attention | Orange | "Pipeline delayed. Check collectors." |
| **Error** | Error | Red | "DLQ: 2 failed signals." |

**Behavior:**
- Auto-dismiss: 5s (success), 8s (event), 12s (warning/error)
- Click → navigate to relevant page
- "Stay Ahead with Swift." reinforces brand on every notification
- Sound: optional, off by default

### Notification Center (Bell)

- **Dropdown** — Dark Slate background, matches notification bubbles
- **Header:** "Notifications" + "Mark all read"
- **Items:** Same anatomy as above, compact
- **Grouped:** Events, System, Alerts
- **Empty state:** "No new notifications. Stay Ahead."

### Push / External (SaaS)

- **Email digest:** Branded subject: "Swift: Your daily intelligence digest"
- **Web push:** Bird icon, "Stay Ahead with Swift." in body
- **Slack/Telegram:** Via OpenClaw — configured in Alerts page

---

## 6. Suggested Actions

*"Stay Ahead" — actions should feel proactive and timely.*

### Contextual Actions (Event Card)

| Context | Actions | Styling |
|---------|---------|---------|
| **Event card** | View details, Share link, Add to watchlist | Electric Blue for primary |
| **Event detail** | Export, Create alert rule, Send to channel | Orange for "Create alert" |
| **Ingest** | Ingest another, View pipeline status | Electric Blue Submit |
| **DLQ** | Retry, Dismiss, View raw | Orange Retry, muted Dismiss |

### Suggested Actions (AI / Smart)

- **"Events like this"** — similar events; badge: "Stay Ahead"
- **"Recommended channels"** — suggest Telegram/Discord for this event type
- **"Quick ingest"** — "Paste URL" → fetch and pre-fill; orange "Fetch" button
- **"What's next?"** — proactive prompt when feed is quiet

### Command Palette (`Cmd+K` / `Ctrl+K`)

- **Header:** "Swift" + bird icon; "Stay Ahead."
- Quick nav: "Go to Events", "New ingest"
- Search: "earthquake Chile"
- Actions: "Trigger pipeline", "Open DLQ"

---

## 7. Forms — Layout & Display

### Ingest Form (Primary Analyst Form)

**Layout:** Two-column on desktop, stacked on mobile

```
┌─────────────────────────────────────────────────────────────┐
│  Ingest Signal                                    [Submit]  │
├─────────────────────────────────────────────────────────────┤
│  Content *                                                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ [Textarea - min 20 chars, max 10000]                    │ │
│  │ Paste or type signal content...                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  Source Type *          Source Name                          │
│  [Dropdown: RSS, News API, Twitter, Manual, ...]  [________]│
│                                                              │
│  URL (optional)                                              │
│  [________________________________________________]          │
│                                                              │
│  [ ] Add another (batch mode)                                │
└─────────────────────────────────────────────────────────────┘
```

**UX:**
- **Content** first — most important
- **Source** pre-filled from context (e.g. "Manual" if pasted)
- **URL** optional, for traceability
- **Batch:** Expand to add more signals; show count badge
- **Validation:** Inline errors, character count
- **Success:** Branded toast ("Stay Ahead with Swift.") + optional "Ingest another" reset
- **Submit button:** Electric Blue; focus ring in orange

### Filter Form (Events Page)

**Layout:** Inline, collapsible

```
[Search...] [Type ▼] [Severity ▼] [Location] [Date range] [Apply] [Reset]
```

- **Sticky** below header when scrolling
- **Chips** for active filters: `Type: Politics ×  Severity: 3+ ×`
- **Presets:** "Critical only", "Last 24h", "My watchlist"

### Auth Forms (Login / Register)

**Layout:** Centered card, minimal

- **Login:** Email/username, Password, Remember, Forgot?
- **Register:** Username, Email, Password, Role (if admin invites)
- **No clutter** — single column, clear CTAs

### Settings Forms

- **Tabs:** Profile, Notifications, Integrations, Billing (SaaS)
- **Sections** with headings
- **Save** per section or global "Save all"

---

## 8. Event Feed & Cards

### Event Card (List View)

```
┌─────────────────────────────────────────────────────────────┐
│ [4]  Earthquake strikes central Chile                       │
│      POLITICS · Reuters · 12 min ago                        │
│      Santiago, Chile                                         │
│      Confidence: 87%                                        │
└─────────────────────────────────────────────────────────────┘
```

- **Severity badge** left (color-coded per scale; orange for 3–4)
- **Title** Montserrat Bold, truncate at 80 chars
- **Meta:** Type, source, time — Text Secondary
- **Location** if present
- **Confidence** subtle
- **Hover:** Slight lift, Electric Blue border highlight
- **Click:** Navigate to detail

### Event Card (Compact / Grid)

- Smaller cards for density
- Toggle: List | Grid
- **Infinite scroll** or pagination (user preference)

### Event Detail Page

- **Hero:** Title, severity, type, timestamp
- **Description** with expand
- **Sources** as chips/links
- **Entities** (people, orgs, locations) as tags
- **Map** if lat/long
- **Actions:** Share, Export, Create alert

---

## 9. SaaS Considerations

### Multi-Tenancy

- **Workspace switcher** in header (if user has multiple orgs)
- **Org context** in API calls
- **Billing** tied to org

### Pricing Tiers (Frontend Impact)

| Tier | Events/month | Users | Features |
|------|---------------|-------|----------|
| Free | 1K | 1 | Basic feed, 7-day retention |
| Pro | 50K | 5 | Full features, 90-day retention |
| Enterprise | Unlimited | Unlimited | SSO, SLA, custom |

**UI implications:**
- **Upgrade prompts** when limit approached
- **Feature gates** — e.g. "Upgrade to Pro for OpenClaw alerts"
- **Usage dashboard** — events ingested, API calls

### Billing & Account

- **Settings → Billing:** Plan, usage, payment method
- **Team:** Invite users, roles (admin, analyst, viewer)
- **Audit log:** Who did what (Enterprise)

### Onboarding (SaaS)

- **First login:** Welcome wizard
  1. Connect first source (optional)
  2. Set notification preferences
  3. View sample event
- **Empty states:** "No events yet — ingest a signal or wait for pipeline"

### Landing Page (SaaS)

- **Hero:** Sky Gradient (blue → orange) over blurred city skyline; "Swift Stay Ahead." logo in white; subhead: "Event intelligence that keeps you ahead"
- **Features:** Real-time, AI classification, Multi-source, Alerts — each with bird icon accent
- **Pricing:** 3 tiers, toggle monthly/annual; Electric Blue for selected tier
- **CTA:** "Start free trial" / "Book demo" — Electric Blue or Orange buttons
- **Social proof:** Logos, testimonials
- **Footer:** Docs, Status, Privacy, Terms — Montserrat

---

## 10. Responsive & Accessibility

- **Breakpoints:** Mobile (<768), Tablet (768–1024), Desktop (1024+)
- **Mobile:** Hamburger nav, stacked forms, swipeable event cards
- **Keyboard:** Full nav, focus indicators, skip links
- **Screen readers:** ARIA labels, live regions for notifications
- **Reduced motion:** Respect `prefers-reduced-motion`

---

## 11. Tech Stack Suggestion

| Layer | Recommendation |
|-------|-----------------|
| **Framework** | React + TypeScript or Next.js (if SSR/SEO needed for marketing) |
| **Styling** | Tailwind CSS + design tokens |
| **State** | TanStack Query (server state) + Zustand (client) |
| **Forms** | React Hook Form + Zod |
| **Charts** | Recharts or Tremor |
| **Maps** | Mapbox GL (you have the key) |
| **Icons** | Lucide or Heroicons |

---

## 12. Implementation Order

1. **Auth + shell** — Login, layout, nav
2. **Event feed** — List, filters, cards
3. **Event detail** — Full view, map
4. **Ingest form** — Single, then batch
5. **Pipeline page** — Status, stats
6. **Notifications** — In-app, center
7. **Alerts** — Preferences, channels
8. **Admin** — DLQ, users, keys
9. **Settings** — Profile, theme
10. **Marketing site** — If SaaS
11. **Billing** — If SaaS

---

## 13. Design Tokens (CSS/Tailwind)

```css
/* Swift brand tokens (from concept board) */
--swift-electric-blue: #007AFF;
--swift-vibrant-orange: #FF9500;
--swift-bird-streak: #FFF500;
--swift-sky-start: #5EDFFF;
--swift-sky-end: #00BFFF;
--swift-dark-slate: #0A1628;
--swift-surface: #142338;
--swift-border: #1E3A5F;
--swift-text-primary: #FFFFFF;
--swift-text-secondary: #8BA3C7;
--swift-font-heading: 'Montserrat', sans-serif;
```

---

*This document refines the Swift Event Intelligence frontend design using the **Swift — Stay Ahead.** branding concept board. Iterate based on user feedback and analytics.*
